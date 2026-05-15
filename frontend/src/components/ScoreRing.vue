<script setup>
import { computed } from "vue";
import VChart from "vue-echarts";

const props = defineProps({
  /** 0–100 */
  value: { type: Number, default: 0 },
  title: { type: String, default: "得分" }
});

const option = computed(() => ({
  series: [
    {
      type: "gauge",
      startAngle: 210,
      endAngle: -30,
      min: 0,
      max: 100,
      splitNumber: 5,
      radius: "92%",
      center: ["50%", "58%"],
      progress: {
        show: true,
        width: 14,
        roundCap: true,
        itemStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 1,
            y2: 0,
            colorStops: [
              { offset: 0, color: "#6366f1" },
              { offset: 1, color: "#a855f7" }
            ]
          }
        }
      },
      axisLine: {
        lineStyle: {
          width: 14,
          color: [[1, "#e2e8f0"]]
        }
      },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      pointer: { show: false },
      anchor: { show: false },
      title: {
        show: true,
        offsetCenter: [0, "72%"],
        fontSize: 12,
        color: "#64748b"
      },
      detail: {
        valueAnimation: true,
        fontSize: 28,
        fontWeight: 700,
        color: "#0f172a",
        offsetCenter: [0, "28%"],
        formatter: "{value}"
      },
      data: [{ value: Math.round(props.value * 100) / 100, name: props.title }]
    }
  ]
}));
</script>

<template>
  <div class="score-ring">
    <VChart class="score-ring__chart" :option="option" autoresize />
  </div>
</template>

<style scoped>
.score-ring {
  width: 100%;
  max-width: 220px;
  margin: 0 auto;
}

.score-ring__chart {
  height: 200px;
  width: 100%;
}
</style>
