"use client";

import { useEffect, useState, useTransition } from "react";

import { PACK_UI_DEFINITIONS } from "./guided-pack-config";
import type {
  GuidedField,
  GuidedFormState,
  PackUiDefinition,
} from "./guided-pack-types";
import { ExplainabilityPanel, ResultPanel } from "./workspace-output-panels";
import { buildErrorMessage, fetchJson } from "./workspace-runtime";
import type {
  EvaluationResult,
  JsonObject,
  MultiEvaluationResult,
  PackDetail,
  PackSummary,
} from "./workspace-types";
import {
  ActionButton,
  EmptyState,
  ErrorBanner,
  MetricCard,
  SegmentedField,
  SelectField,
  StatusBanner,
  SummaryRow,
  TextList,
} from "./workspace-ui";

const SELECTED_PACK_STORAGE_KEY = "border-checker-selected-pack";

const COUNTRY_OPTIONS = [
  { value: "EU", label: "EU / EEA" },
  { value: "Korea", label: "Korea" },
  { value: "Brazil", label: "Brazil" },
  { value: "Taiwan", label: "Taiwan" },
  { value: "Saudi Arabia", label: "Saudi Arabia" },
];

const CLOUD_PROVIDER_OPTIONS = [
  { value: "manual", label: "수동 입력" },
  { value: "aws", label: "AWS Mock" },
  { value: "azure", label: "Azure Mock" },
];

const COUNTRY_TO_EXPORT_PACK: Record<string, string> = {
  EU: "gdpr",
  Korea: "korea_pipa",
  Brazil: "lgpd",
  "Saudi Arabia": "saudi_pdpl",
  Taiwan: "taiwan",
};

const COUNTRY_TO_DESTINATION_PACK: Record<string, string> = {
  EU: "gdpr_destination",
  Korea: "korea_pipa_destination",
  Brazil: "lgpd_destination",
  "Saudi Arabia": "saudi_pdpl_destination",
  Taiwan: "taiwan_destination",
};

const PACK_LABELS: Record<string, string> = {
  gdpr: "GDPR",
  korea_pipa: "Korea PIPA",
  lgpd: "Brazil LGPD",
  saudi_pdpl: "Saudi PDPL",
  taiwan: "Taiwan PDPA",
  gdpr_destination: "GDPR Destination Compliance",
  korea_pipa_destination: "Korea PIPA Destination Compliance",
  lgpd_destination: "Brazil LGPD Destination Compliance",
  saudi_pdpl_destination: "Saudi PDPL Destination Compliance",
  taiwan_destination: "Taiwan PDPA Destination Compliance",
};

type ScreenMode = "intro" | "step" | "review" | "result";

function renderField(
  field: GuidedField,
  state: GuidedFormState,
  onChange: (key: string, value: string) => void,
) {
  if (field.kind === "select") {
    return (
      <SelectField
        label={field.label}
        helper={field.helper}
        tooltip={field.tooltip}
        value={state[field.key] ?? ""}
        onChange={(value) => onChange(field.key, value)}
        options={field.options}
      />
    );
  }

  return (
    <SegmentedField
      label={field.label}
      helper={field.helper}
      tooltip={field.tooltip}
      value={state[field.key] ?? ""}
      onChange={(value) => onChange(field.key, value)}
      options={field.options}
    />
  );
}

function optionLabelForField(field: GuidedField, rawValue: string) {
  if (rawValue === "") {
    return "";
  }

  const matched = field.options.find((option) => option.value === rawValue);
  if (matched) {
    return matched.label;
  }

  if (rawValue === "true") {
    return "예";
  }
  if (rawValue === "false") {
    return "아니오";
  }
  if (rawValue === "unknown") {
    return "잘 모르겠음";
  }

  return rawValue;
}

function collectVisibleStepFields(
  definition: PackUiDefinition,
  state: GuidedFormState,
  stepIndex: number,
) {
  const step = definition.steps[stepIndex];
  return step.fields.filter(
    (field) => !field.visibleIf || field.visibleIf(state),
  );
}

function collectStepMissingFields(
  definition: PackUiDefinition,
  state: GuidedFormState,
  stepIndex: number,
) {
  return collectVisibleStepFields(definition, state, stepIndex)
    .filter((field) => field.required)
    .filter((field) => !state[field.key])
    .map((field) => field.label);
}

function buildReviewSections(
  definition: PackUiDefinition,
  state: GuidedFormState,
) {
  return definition.steps
    .map((step, stepIndex) => {
      const rows = collectVisibleStepFields(definition, state, stepIndex)
        .map((field) => ({
          label: field.label,
          value: optionLabelForField(field, state[field.key] ?? ""),
        }))
        .filter((row) => row.value);

      return {
        id: step.id,
        title: step.title,
        description: step.description,
        rows,
      };
    })
    .filter((section) => section.rows.length > 0);
}

export function GuidedSingleFlowPage() {
  const [packSummaries, setPackSummaries] = useState<PackSummary[]>([]);
  const [selectedPackId, setSelectedPackId] = useState("gdpr");
  const [packDetail, setPackDetail] = useState<PackDetail | null>(null);
  const [formState, setFormState] = useState<GuidedFormState>({});
  const [screenMode, setScreenMode] = useState<ScreenMode>("intro");
  const [stepIndex, setStepIndex] = useState(0);
  const [evaluationResult, setEvaluationResult] =
  useState<EvaluationResult | null>(null);
  const [multiEvaluationResult, setMultiEvaluationResult] =
  useState<MultiEvaluationResult | null>(null);
  const [originCountry, setOriginCountry] = useState("EU");
  const [destinationCountry, setDestinationCountry] = useState("Brazil");
  const [cloudProvider, setCloudProvider] = useState("aws");
  const [statusMessage, setStatusMessage] = useState(
    "법제를 고르고 단계별 질문에 답하면 마지막 검토 화면에서 평가를 실행합니다.",
  );
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isBusy, setIsBusy] = useState(false);
  const [storageReady, setStorageReady] = useState(false);
  const [, startTransition] = useTransition();

  const packDefinition =
    PACK_UI_DEFINITIONS[selectedPackId] ?? PACK_UI_DEFINITIONS.gdpr;
  const autoPrimaryPackId =
  COUNTRY_TO_EXPORT_PACK[originCountry] ?? selectedPackId;

  const autoReferencePackId =
  COUNTRY_TO_DESTINATION_PACK[destinationCountry];
  const currentStep = packDefinition.steps[stepIndex];
  const visibleFields = collectVisibleStepFields(
    packDefinition,
    formState,
    stepIndex,
  );
  const currentStepMissing = collectStepMissingFields(
    packDefinition,
    formState,
    stepIndex,
  );
  const overallMissing = packDefinition.validate(formState);
  const advisoryNotes = packDefinition.buildAdvisoryNotes(formState);
  const reviewSections = buildReviewSections(packDefinition, formState);
  const progressPercent =
    screenMode === "intro"
      ? 8
      : screenMode === "review"
        ? 92
        : ((stepIndex + 1) / packDefinition.steps.length) * 100;

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      try {
        const summaries = await fetchJson<PackSummary[]>("/api/v1/packs");
        const supportedSummaries = summaries.filter(
          (pack) => pack.pack_id in PACK_UI_DEFINITIONS,
        );
        const storedPackId =
          window.localStorage.getItem(SELECTED_PACK_STORAGE_KEY) ?? "gdpr";
        const nextPackId =
          storedPackId in PACK_UI_DEFINITIONS ? storedPackId : "gdpr";

        if (!cancelled) {
          startTransition(() => {
            setPackSummaries(supportedSummaries);
            setSelectedPackId(nextPackId);
          });
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(buildErrorMessage(error));
        }
      }
    }

    void bootstrap();
    return () => {
      cancelled = true;
    };
  }, [startTransition]);

  useEffect(() => {
    let cancelled = false;
    const definition = PACK_UI_DEFINITIONS[selectedPackId];
    if (!definition) {
      return;
    }

    window.localStorage.setItem(SELECTED_PACK_STORAGE_KEY, selectedPackId);

    const storedState = window.localStorage.getItem(definition.storageKey);
    let nextState = { ...definition.defaultState };
    if (storedState) {
      try {
        nextState = {
          ...definition.defaultState,
          ...(JSON.parse(storedState) as GuidedFormState),
        };
      } catch {}
    }

    startTransition(() => {
      setFormState(nextState);
      setStepIndex(0);
      setScreenMode("intro");
      setEvaluationResult(null);
      setMultiEvaluationResult(null);
      setStorageReady(true);
      setStatusMessage(
        `${definition.label} 질문 흐름을 불러왔습니다. 시작하기를 누르면 한 단계씩 진행됩니다.`,
      );
    });

    async function loadDetail() {
      try {
        const detail = await fetchJson<PackDetail>(
          `/api/v1/packs/${selectedPackId}/detail`,
        );
        if (!cancelled) {
          setPackDetail(detail);
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(buildErrorMessage(error));
        }
      }
    }

    void loadDetail();
    return () => {
      cancelled = true;
    };
  }, [selectedPackId, startTransition]);

  useEffect(() => {
    if (!storageReady) {
      return;
    }

    window.localStorage.setItem(
      packDefinition.storageKey,
      JSON.stringify(formState),
    );
  }, [formState, packDefinition.storageKey, storageReady]);

  function updateField(key: string, value: string) {
    setErrorMessage(null);
    setFormState((current) => {
      const next = { ...current, [key]: value };

      if (key === "derogation_used" && value !== "true") {
        next.derogation_type = "";
      }
      if (key === "transfer_exception_used" && value !== "true") {
        next.transfer_exception_type = "";
      }
      if (key === "dpia_required" && value !== "true") {
        next.dpia_completed = "";
      }
      if (key === "dpo_required" && value !== "true") {
        next.dpo_assigned = "";
      }
      if (key === "processing_legal_basis" && value !== "consent") {
        next.consent_withdrawal_process_ready = "unknown";
      }
      if (key === "contains_sensitive_data" && value !== "true") {
        next.special_category_condition_met = "unknown";
        next.explicit_consent_for_sensitive_data = "unknown";
      }

      return next;
    });
  }

  function updateOriginCountry(value: string) {
  setOriginCountry(value);
  setErrorMessage(null);

  const nextPackId = COUNTRY_TO_EXPORT_PACK[value];
  if (nextPackId && nextPackId !== selectedPackId && nextPackId in PACK_UI_DEFINITIONS) {
    setSelectedPackId(nextPackId);
  }
}

  function resetCurrentPack() {
    window.localStorage.removeItem(packDefinition.storageKey);
    startTransition(() => {
      setFormState({ ...packDefinition.defaultState });
      setStepIndex(0);
      setScreenMode("intro");
      setEvaluationResult(null);
      setMultiEvaluationResult(null);
      setErrorMessage(null);
      setStatusMessage("입력을 초기화했습니다. 다시 시작해 주세요.");
    });
  }

  async function runEvaluation() {
  setIsBusy(true);
  setErrorMessage(null);

  try {
    const basePayload = packDefinition.buildPayload(formState) as {
      aws_data: JsonObject;
      policy_data: JsonObject;
    };

    const awsData: JsonObject = {
      ...basePayload.aws_data,
      target_region:
      basePayload.policy_data["target_region"] ??
      basePayload.aws_data["target_region"] ??
      basePayload.aws_data["current_region"],
      target_country: destinationCountry,
    };

    const response = await fetchJson<MultiEvaluationResult>(
      "/api/v1/evaluate-multi",
      {
        method: "POST",
        body: JSON.stringify({
          origin_country: originCountry,
          destination_country: destinationCountry,
          aws_data: awsData,
          policy_data: {
  ...basePayload.policy_data,

  // reference pack 데모 안정화를 위한 공통 필드
  processing_purpose_defined:
    basePayload.policy_data["processing_purpose_defined"] ?? true,
  data_minimized:
    basePayload.policy_data["data_minimized"] ?? true,
  retention_period_defined:
    basePayload.policy_data["retention_period_defined"] ?? true,

  // 국가별 정책팩 필드명 차이 보정
  data_subject_connection:
    basePayload.policy_data["data_subject_connection"] ??
    basePayload.policy_data["data_subject_region"] ??
    originCountry,

  processing_legal_basis:
    basePayload.policy_data["processing_legal_basis"] ??
    basePayload.policy_data["lawful_basis"] ??
    "consent",

  transfer_exception_used:
    basePayload.policy_data["transfer_exception_used"] ??
    basePayload.policy_data["derogation_used"] ??
    false,
},
          include_destination_reference: true,
          extra_pack_ids: [],
          use_mock_cloud: cloudProvider !== "manual",
          cloud_provider: cloudProvider,
          cloud_resource: {
  region:
    awsData["target_region"] ??
    awsData["current_region"] ??
    "sa-east-1",
  resource_type: "s3",
  contains_sensitive_data:
    awsData["contains_sensitive_data"] ?? true,
  encryption_at_rest:
    awsData["encryption_at_rest"] ?? true,
  encryption_in_transit:
    awsData["encryption_in_transit"] ?? true,
  access_control_in_place:
    awsData["access_control_in_place"] ?? true,
},
        }),
      },
    );

    const primaryEvaluationResult = response.primary_result.result;

    if (!primaryEvaluationResult) {
      throw new Error(
        response.primary_result.error ??
          "주 적용 정책팩 평가 결과를 불러오지 못했습니다.",
      );
    }

    startTransition(() => {
      setMultiEvaluationResult(response);
      setEvaluationResult(primaryEvaluationResult);
      setScreenMode("result");
      setStatusMessage(
        "동시 적용 평가가 완료되었습니다. 주 적용 법령과 참고 검토 결과를 확인해 주세요.",
      );
    });
  } catch (error) {
    setErrorMessage(buildErrorMessage(error));
  } finally {
    setIsBusy(false);
  }
}

  const availablePackCards = Object.values(PACK_UI_DEFINITIONS).map((definition) => {
    const matchedSummary = packSummaries.find(
      (pack) => pack.pack_id === definition.id,
    );

    return (
      matchedSummary ?? {
        pack_id: definition.id,
        pack_name: definition.label,
        jurisdiction: definition.label,
        version: "1.0.0",
        description: definition.subtitle,
        rule_count: definition.steps.length,
        supported_decisions: [],
        covered_categories: [],
        disclaimer: "",
      }
    );
  });

  if (screenMode === "result" && evaluationResult) {
    return (
      <main className="app-shell min-h-screen overflow-visible">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-5 px-4 py-6 sm:px-6 lg:px-8">
          <section className="glass-panel relative z-[999] !overflow-visible rounded-lg border border-[var(--color-line)] p-5">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-muted)]">
                  Evaluation Complete
                </p>
                <h1 className="mt-3 text-3xl font-bold tracking-tight text-[var(--color-ink)] sm:text-4xl">
                  {packDefinition.label} 평가 결과
                </h1>
                <p className="mt-2 max-w-2xl text-sm leading-7 text-[var(--color-muted)]">
                  입력을 모두 확인한 뒤 최종 결과를 생성했습니다. 필요하면 다시
                  입력 화면으로 돌아가 수정할 수 있습니다.
                </p>
              </div>
              <div className="flex flex-wrap gap-3">
                <ActionButton
                  label="입력 다시 보기"
                  onClick={() => setScreenMode("review")}
                  variant="secondary"
                />
                <ActionButton
                  label="경로 바꾸기"
                  onClick={() => setScreenMode("intro")}
                  variant="secondary"
                />
                <ActionButton label="새로 시작" onClick={resetCurrentPack} />
              </div>
            </div>
          </section>

          <section className="grid gap-5">
  {multiEvaluationResult ? (
    <section className="glass-panel relative z-[100] overflow-visible rounded-lg border border-[var(--color-line)] p-5">
      <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-muted)]">
        Multi-policy Evaluation
      </p>
      <h2 className="mt-2 text-xl font-bold text-[var(--color-ink)]">
        동시 적용 결과 요약
      </h2>
      <p className="mt-3 text-sm leading-7 text-[var(--color-muted)]">
        {multiEvaluationResult.overall_summary}
      </p>

      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <div className="rounded-lg border border-[var(--color-line)] bg-[var(--color-surface-strong)] p-4">
          <p className="text-xs font-semibold text-[var(--color-muted)]">
            이전 경로
          </p>
          <p className="mt-2 text-lg font-semibold text-[var(--color-ink)]">
            {multiEvaluationResult.origin_country} →{" "}
            {multiEvaluationResult.destination_country}
          </p>
        </div>
        <div className="rounded-lg border border-[var(--color-line)] bg-[var(--color-surface-strong)] p-4">
          <p className="text-xs font-semibold text-[var(--color-muted)]">
            주 적용 정책
          </p>
          <p className="mt-2 text-lg font-semibold text-[var(--color-ink)]">
            {PACK_LABELS[multiEvaluationResult.primary_pack_id] ??
              multiEvaluationResult.primary_pack_id}
          </p>
        </div>
        <div className="rounded-lg border border-[var(--color-line)] bg-[var(--color-surface-strong)] p-4">
          <p className="text-xs font-semibold text-[var(--color-muted)]">
            참고 검토 정책
          </p>
          <p className="mt-2 text-lg font-semibold text-[var(--color-ink)]">
            {multiEvaluationResult.reference_pack_ids.length > 0
              ? multiEvaluationResult.reference_pack_ids
                  .map((id) => PACK_LABELS[id] ?? id)
                  .join(", ")
              : "없음"}
          </p>
        </div>
      </div>

      {multiEvaluationResult.overall_warnings.length > 0 ? (
        <div className="mt-4 rounded-lg border border-[var(--color-warning)] bg-[var(--color-warning-soft)] p-4">
          <p className="text-sm font-semibold text-[var(--color-warning)]">
            참고 검토 경고
          </p>
          <ul className="mt-2 space-y-1 text-sm leading-7 text-[var(--color-muted)]">
            {multiEvaluationResult.overall_warnings.map((warning) => (
              <li key={warning}>- {warning}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {multiEvaluationResult.results_by_pack.map((item) => (
          <div
            key={`${item.role}-${item.pack_id}`}
            className="rounded-lg border border-[var(--color-line)] bg-[var(--color-surface-strong)] p-4"
          >
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-muted)]">
              {item.role}
            </p>
            <p className="mt-2 text-base font-semibold text-[var(--color-ink)]">
              {PACK_LABELS[item.pack_id] ?? item.pack_id}
            </p>
            <p className="mt-1 text-sm text-[var(--color-muted)]">
              판정: {item.final_decision ?? "오류"}
            </p>
            {item.error ? (
              <p className="mt-2 text-sm leading-7 text-[var(--color-warning)]">
                {item.error}
              </p>
            ) : null}
          </div>
        ))}
      </div>
    </section>
  ) : null}

  <ResultPanel evaluationResult={evaluationResult} />
  <ExplainabilityPanel
    evaluationResult={evaluationResult}
    mergePreview={evaluationResult.merged_input}
  />
</section>

          <footer className="rounded-lg border border-[var(--color-line)] bg-[var(--color-surface-strong)] px-5 py-4 text-sm leading-7 text-[var(--color-muted)]">
            <p className="font-semibold text-[var(--color-ink)]">Disclaimer</p>
            <p>
              Border Checker는 정책 기반 의사결정 지원 도구입니다. 실제 운영
              반영 전에는 법무, 프라이버시, 보안 담당자가 사실관계와 문서를 함께
              검토해야 합니다.
            </p>
          </footer>
        </div>
      </main>
    );
  }

  return (
    <main className="app-shell min-h-screen overflow-hidden">
      <div className="mx-auto flex min-h-screen w-full max-w-4xl flex-col gap-5 px-4 py-6 sm:px-6">
        <header className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="rounded-md border border-[var(--color-accent)] bg-[var(--color-accent-soft)] px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-accent)]">
              Border Checker
            </span>
            <span className="text-sm text-[var(--color-muted)]">
              Guided Intake Flow
            </span>
          </div>
          {screenMode !== "intro" ? (
            <button
              type="button"
              onClick={() => setScreenMode("intro")}
              className="text-sm font-medium text-[var(--color-accent)] underline-offset-4 hover:underline"
            >
              경로 다시 선택
            </button>
          ) : null}
        </header>

        <section className="glass-panel rounded-lg border border-[var(--color-line)] p-5">
  <div className="grid gap-4 md:grid-cols-3">
    <div>
      <label className="text-sm font-semibold text-[var(--color-ink)]">
        출발 국가
      </label>
      <p className="mt-1 text-sm leading-6 text-[var(--color-muted)]">
        데이터가 나가는 국가입니다. 이 국가의 법령을 주 적용 정책으로 사용합니다.
      </p>
      <select
        value={originCountry}
        onChange={(event) => updateOriginCountry(event.target.value)}
        className="mt-3 w-full rounded-lg border border-[var(--color-line)] bg-white px-4 py-3 text-sm text-[var(--color-ink)] outline-none transition focus:border-[var(--color-accent)] focus:ring-4 focus:ring-[var(--color-accent-soft)]"
      >
        {COUNTRY_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>

    <div>
      <label className="text-sm font-semibold text-[var(--color-ink)]">
        도착 국가
      </label>
      <p className="mt-1 text-sm leading-6 text-[var(--color-muted)]">
        데이터가 도착하는 국가입니다. 참고 검토 정책으로 표시됩니다.
      </p>
      <select
        value={destinationCountry}
        onChange={(event) => {
          setDestinationCountry(event.target.value);
          setErrorMessage(null);
        }}
        className="mt-3 w-full rounded-lg border border-[var(--color-line)] bg-white px-4 py-3 text-sm text-[var(--color-ink)] outline-none transition focus:border-[var(--color-accent)] focus:ring-4 focus:ring-[var(--color-accent-soft)]"
      >
        {COUNTRY_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>

    <div>
      <label className="text-sm font-semibold text-[var(--color-ink)]">
        클라우드 연동
      </label>
      <p className="mt-1 text-sm leading-6 text-[var(--color-muted)]">
        현재는 발표용 Mock API로 리전/보안 입력을 보완합니다.
      </p>
      <select
        value={cloudProvider}
        onChange={(event) => {
          setCloudProvider(event.target.value);
          setErrorMessage(null);
        }}
        className="mt-3 w-full rounded-lg border border-[var(--color-line)] bg-white px-4 py-3 text-sm text-[var(--color-ink)] outline-none transition focus:border-[var(--color-accent)] focus:ring-4 focus:ring-[var(--color-accent-soft)]"
      >
        {CLOUD_PROVIDER_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  </div>

  <div className="mt-4 rounded-lg border border-[var(--color-line)] bg-[var(--color-surface-strong)] p-4 text-sm leading-7">
    <p className="font-semibold text-[var(--color-ink)]">
      자동 적용 정책
    </p>
    <p className="mt-1 text-[var(--color-muted)]">
      주 적용:{" "}
      <span className="font-semibold text-[var(--color-ink)]">
        {PACK_LABELS[autoPrimaryPackId] ?? autoPrimaryPackId}
      </span>
      {" · "}
      참고 검토:{" "}
      <span className="font-semibold text-[var(--color-ink)]">
        {autoReferencePackId && autoReferencePackId !== autoPrimaryPackId
          ? PACK_LABELS[autoReferencePackId] ?? autoReferencePackId
          : "없음"}
      </span>
    </p>
  </div>
</section>
        

        <div className="relative z-0 flex flex-1 items-center justify-center">
          <section className="glass-panel w-full overflow-hidden rounded-lg border border-[var(--color-line)] px-5 py-6 sm:px-6 sm:py-7">
            <div
              key={`${selectedPackId}-${screenMode}-${stepIndex}`}
              className="screen-enter"
            >
            {screenMode === "intro" ? (
              <div className="space-y-7">
                <div className="space-y-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-muted)]">
                    Step 0
                  </p>
                  <h1 className="text-3xl font-bold tracking-tight text-[var(--color-ink)] sm:text-4xl">
                    데이터 이전 경로를 확인해 주세요
                  </h1>
                  <p className="max-w-2xl text-sm leading-7 text-[var(--color-muted)]">
                    출발 국가와 도착 국가를 기준으로 주 적용 법령과 참고 검토 법령이 자동 선택됩니다.
                  </p>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
  <div className="rounded-lg border border-[var(--color-accent)] bg-[var(--color-accent-soft)] p-5">
    <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-muted)]">
      주 적용 법령
    </p>
    <h3 className="mt-2 text-lg font-semibold text-[var(--color-ink)]">
      {PACK_LABELS[autoPrimaryPackId] ?? autoPrimaryPackId}
    </h3>
    <p className="mt-2 text-sm leading-6 text-[var(--color-muted)]">
      출발 국가인 {originCountry} 기준으로 최종 판정에 사용됩니다.
    </p>
  </div>

  <div className="rounded-lg border border-[var(--color-line)] bg-[var(--color-surface-strong)] p-5">
    <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-muted)]">
      참고 검토 법령
    </p>
    <h3 className="mt-2 text-lg font-semibold text-[var(--color-ink)]">
      {autoReferencePackId && autoReferencePackId !== autoPrimaryPackId
        ? PACK_LABELS[autoReferencePackId] ?? autoReferencePackId
        : "없음"}
    </h3>
    <p className="mt-2 text-sm leading-6 text-[var(--color-muted)]">
      도착 국가인 {destinationCountry} 기준 참고 결과로 함께 표시됩니다.
    </p>
  </div>
</div>

                <div className="grid gap-3 sm:grid-cols-3">
                  <MetricCard
  label="주 적용 정책"
  value={PACK_LABELS[autoPrimaryPackId] ?? autoPrimaryPackId}
/>
                  <MetricCard
  label="적용 방식"
  value="출발국 중심 + 도착국 참고"
/>
                  <MetricCard
                    label="규칙 수"
                    value={packDetail ? `${packDetail.rule_count} rules` : "로딩 중"}
                  />
                </div>

                {packDetail ? (
                  <TextList
                    title="검토 가이드"
                    items={packDetail.review_guidance}
                  />
                ) : (
                  <EmptyState
                    title="팩 정보를 불러오는 중입니다."
                    description="선택한 팩의 질문 구조와 메타데이터를 준비하고 있습니다."
                  />
                )}

                <div className="flex flex-wrap gap-3">
                  <ActionButton
                    label="검토 입력 시작"
                    onClick={() => {
                      setStepIndex(0);
                      setScreenMode("step");
                      setStatusMessage(
                        `${packDefinition.label} 질문을 시작합니다. 각 단계마다 필요한 항목만 보여드립니다.`,
                      );
                    }}
                  />
                  <ActionButton
                    label="입력 초기화"
                    onClick={resetCurrentPack}
                    variant="secondary"
                  />
                </div>
              </div>
            ) : null}

            {screenMode === "step" ? (
              <div className="space-y-7">
                <div className="space-y-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-muted)]">
                    Step {stepIndex + 1}
                  </p>
                  <h1 className="text-3xl font-bold tracking-tight text-[var(--color-ink)]">
                    {currentStep.title}
                  </h1>
                  <p className="text-sm leading-7 text-[var(--color-muted)]">
                    {currentStep.description}
                  </p>
                  <div className="pt-2">
                    <div className="flex items-center justify-between text-xs text-[var(--color-muted)]">
                      <span>진행률</span>
                      <span>{Math.round(progressPercent)}%</span>
                    </div>
                    <div className="progress-track mt-2">
                      <div
                        className="progress-fill"
                        style={{ width: `${progressPercent}%` }}
                      />
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  {packDefinition.steps.map((step, index) => (
                    <span
                      key={step.id}
                      className={`rounded-md border px-3 py-1.5 text-sm ${
                        index === stepIndex
                          ? "border-[var(--color-accent)] bg-[var(--color-accent-soft)] text-[var(--color-accent)]"
                          : "border-[var(--color-line)] bg-[var(--color-surface-strong)] text-[var(--color-muted)]"
                      }`}
                    >
                      {index + 1}. {step.title}
                    </span>
                  ))}
                </div>

                <div className="grid gap-5">
                  {visibleFields.map((field) => (
                    <div key={field.key}>{renderField(field, formState, updateField)}</div>
                  ))}
                </div>

                <TextList title="입력 안내" items={advisoryNotes} />
                <StatusBanner message={statusMessage} />
                {errorMessage ? <ErrorBanner message={errorMessage} /> : null}

                <div className="flex flex-wrap gap-3">
                  <ActionButton
                    label="이전"
                    onClick={() =>
                      stepIndex === 0
                        ? setScreenMode("intro")
                        : setStepIndex((value) => value - 1)
                    }
                    variant="secondary"
                  />
                  <ActionButton
                    label={
                      stepIndex === packDefinition.steps.length - 1
                        ? "검토 화면으로"
                        : "다음"
                    }
                    onClick={() => {
                      if (currentStepMissing.length > 0) {
                        setErrorMessage(
                          `${currentStepMissing.join(", ")} 항목을 먼저 선택해 주세요.`,
                        );
                        return;
                      }

                      setErrorMessage(null);
                      if (stepIndex === packDefinition.steps.length - 1) {
                        setScreenMode("review");
                        return;
                      }
                      setStepIndex((value) => value + 1);
                    }}
                  />
                </div>
              </div>
            ) : null}

            {screenMode === "review" ? (
              <div className="space-y-7">
                <div className="space-y-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-muted)]">
                    Final Review
                  </p>
                  <h1 className="text-3xl font-bold tracking-tight text-[var(--color-ink)]">
                    입력 내용을 마지막으로 확인해 주세요
                  </h1>
                  <p className="text-sm leading-7 text-[var(--color-muted)]">
                    여기서 검토가 끝나면 평가를 실행합니다. 결과 화면 전에는 최종
                    판단을 보여주지 않습니다.
                  </p>
                  <div className="pt-2">
                    <div className="flex items-center justify-between text-xs text-[var(--color-muted)]">
                      <span>진행률</span>
                      <span>{Math.round(progressPercent)}%</span>
                    </div>
                    <div className="progress-track mt-2">
                      <div
                        className="progress-fill"
                        style={{ width: `${progressPercent}%` }}
                      />
                    </div>
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-3">
                  <MetricCard label="팩" value={packDefinition.label} />
                  <MetricCard label="남은 필수값" value={`${overallMissing.length}개`} />
                  <MetricCard
                    label="현재 상태"
                    value={overallMissing.length === 0 ? "평가 가능" : "입력 보완 필요"}
                  />
                </div>

                <div className="space-y-4">
                  {reviewSections.map((section) => (
                    <div
                      key={section.id}
                      className="rounded-lg border border-[var(--color-line)] bg-[var(--color-surface-strong)] p-5"
                    >
                      <p className="text-sm font-semibold text-[var(--color-ink)]">
                        {section.title}
                      </p>
                      <p className="mt-1 text-sm leading-6 text-[var(--color-muted)]">
                        {section.description}
                      </p>
                      <div className="mt-3">
                        {section.rows.map((row) => (
                          <SummaryRow
                            key={`${section.id}-${row.label}`}
                            label={row.label}
                            value={row.value}
                          />
                        ))}
                      </div>
                    </div>
                  ))}
                </div>

                <StatusBanner
                  message={
                    overallMissing.length === 0
                      ? "입력이 모두 정리되었습니다. 평가 실행을 누르면 결과 화면으로 이동합니다."
                      : `${overallMissing.join(", ")} 항목이 아직 필요합니다.`
                  }
                />
                {errorMessage ? <ErrorBanner message={errorMessage} /> : null}

                <div className="flex flex-wrap gap-3">
                  <ActionButton
                    label="이전 단계로"
                    onClick={() => {
                      setStepIndex(packDefinition.steps.length - 1);
                      setScreenMode("step");
                    }}
                    variant="secondary"
                  />
                  <ActionButton
                    label="평가 실행"
                    onClick={() => {
                      if (overallMissing.length > 0) {
                        setErrorMessage(
                          `${overallMissing.join(", ")} 항목을 먼저 선택해 주세요.`,
                        );
                        return;
                      }

                      void runEvaluation();
                    }}
                    active={isBusy}
                    disabled={isBusy}
                  />
                </div>
              </div>
            ) : null}
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
