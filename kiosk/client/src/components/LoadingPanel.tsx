interface LoadingPanelProps {
  title: string;
  description?: string;
  /** 0-based index of the step currently running. */
  currentStep?: number;
  totalSteps?: number;
}

export default function LoadingPanel({
  title,
  description,
  currentStep,
  totalSteps,
}: LoadingPanelProps) {
  const showSteps =
    currentStep !== undefined && totalSteps !== undefined && totalSteps > 1;

  return (
    <section className="loading-panel" role="status" aria-live="polite">
      <div className="spinner" aria-hidden="true" />

      <h2 className="loading-title">
        {title}
        <span className="loading-dots" aria-hidden="true">
          <span>.</span>
          <span>.</span>
          <span>.</span>
        </span>
      </h2>

      {description && <p className="loading-detail">{description}</p>}

      {showSteps && (
        <div className="loading-steps" aria-hidden="true">
          {Array.from({ length: totalSteps }, (_, index) => (
            <span
              key={index}
              className={
                index < currentStep
                  ? "dot done"
                  : index === currentStep
                    ? "dot active"
                    : "dot"
              }
            />
          ))}
        </div>
      )}
    </section>
  );
}
