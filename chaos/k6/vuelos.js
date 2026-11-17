import http from "k6/http";
import { check } from "k6";

// Mismo perfil P en la ronda 0 y en la ronda 1. No se cambia entre mediciones.
export const options = {
  scenarios: {
    perfil_p: {
      executor: "ramping-vus",
      stages: [
        { duration: "5s", target: 12 },
        { duration: "20s", target: 12 },
        { duration: "5s", target: 0 },
      ],
    },
  },
  thresholds: {
    http_req_duration: ["p(99)<2000"],
  },
};

const base = __ENV.BASE_URL || "http://127.0.0.1:8011";

export default function () {
  const res = http.get(`${base}/api/v2/entidades/vuelos/random`, {
    headers: { "X-Trace-Id": `k6-${__VU}-${__ITER}` },
    timeout: "6s",
  });
  check(res, { "respondio": (r) => r.status === 200 || r.status === 429 || r.status === 503 });
}

export function handleSummary(data) {
  const ronda = __ENV.RONDA || "0";
  return {
    [`chaos/results/k6-ronda-${ronda}.json`]: JSON.stringify(data, null, 2),
  };
}
