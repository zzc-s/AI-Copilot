import axios from "axios";

const client = axios.create({
  baseURL: "http://127.0.0.1:8000"
});

/**
 * 轮询 Celery 任务状态，直到 SUCCESS / FAILURE 或超时。
 * @param {string} taskId
 * @param {{ intervalMs?: number, timeoutMs?: number }} opts
 */
export async function pollTask(taskId, opts = {}) {
  const intervalMs = opts.intervalMs ?? 800;
  const timeoutMs = opts.timeoutMs ?? 30000;
  const t0 = Date.now();
  while (Date.now() - t0 < timeoutMs) {
    const { data } = await client.get(`/tasks/${taskId}`);
    const st = data.status;
    if (st === "SUCCESS") return data;
    if (st === "FAILURE") throw new Error(data.error || "任务失败");
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  throw new Error("任务超时");
}

export default client;
