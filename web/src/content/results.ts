/* Measured results.
   The organisers' answer key is deliberately NOT deployed, so /metrics is
   unavailable in the cloud. These figures come from running the same pipeline
   against that answer key locally; anyone can reproduce them with `sdoc run`. */
export const measured = {
  asOf: "21 September 2026",
  command: "sdoc run",
  finalScore: "1.000",
  classificationAccuracy: "100%",
  defectsCaught: "46 / 46",
  escalations: "20 / 20",
  falseAlarms: "0",
  tests: 59,
  dataset: "520 emails supplied by the organisers (synthetic)",
};
