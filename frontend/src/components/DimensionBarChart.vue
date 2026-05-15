<script setup>
import { computed } from "vue";
import VChart from "vue-echarts";

const props = defineProps({
  /** [{ name: string, value: number }, ...] */
  items: {
    type: Array,
    default: () => []
  }
});

const option = computed(() => {
  const names = props.items.map((x) => x.name);
  const values = props.items.map((x) => Number(x.value) || 0);
  return {
    grid: { left: 12, right: 24, top: 16, bottom: 8, containLabel: true },
    xAxis: {
      type: "value",
      max: 100,
      splitLine: { lineStyle: { type: "dashed", color: "#e2e8f0" } },
      axisLabel: { color: "#64748b", fontSize: 11 }
    },
    yAxis: {
      type: "category",
      data: names,
      axisLabel: { color: "#334155", fontSize: 12 },
      axisLine: { show: false },
      axisTick: { show: false }
    },
    series: [
      {
        type: "bar",
        data: values,
        barWidth: 14,
        itemStyle: {
          borderRadius: [0, 6, 6, 0],
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 1,
            y2: 0,
            colorStops: [
              { offset: 0, color: "#6366f1" },
              { offset: 1, color: "#c084fc" }
            ]
          }
        },
        label: {
          show: true,
          position: "right",
          formatter: "{c}",
          color: "#475569",
          fontSize: 11
        }
      }
    ],
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } }
  };
});
</script>

<template>
  <div class="bar-chart">
    <VChart class="bar-chart__inner" :option="option" autoresize />
  </div>
</template>

<style scoped>
.bar-chart {
  width: 100%;
  min-height: 160px;
}

.bar-chart__inner {
  height: 200px;
  width: 100%;
}
</style>
