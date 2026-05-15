<script setup>
import { computed } from "vue";
import VChart from "vue-echarts";

const props = defineProps({
  /** [{ name: string, value: number 0-100 }, ...] */
  indicators: {
    type: Array,
    default: () => []
  }
});

const option = computed(() => {
  const list = props.indicators.length
    ? props.indicators
    : [
        { name: "综合", value: 0 },
        { name: "关键词", value: 0 },
        { name: "结构", value: 0 }
      ];
  const indicator = list.map((x) => ({
    name: x.name,
    max: 100
  }));
  const dataVals = list.map((x) => Math.min(100, Math.max(0, Number(x.value) || 0)));
  return {
    radar: {
      indicator,
      radius: "62%",
      splitNumber: 4,
      axisName: {
        color: "#64748b",
        fontSize: 11
      },
      splitArea: {
        areaStyle: {
          color: ["rgba(99,102,241,0.06)", "rgba(99,102,241,0.02)"]
        }
      }
    },
    series: [
      {
        type: "radar",
        data: [
          {
            value: dataVals,
            name: "评分",
            areaStyle: {
              color: "rgba(99, 102, 241, 0.25)"
            },
            lineStyle: {
              color: "#6366f1",
              width: 2
            },
            itemStyle: {
              color: "#6366f1"
            }
          }
        ]
      }
    ],
    tooltip: { trigger: "item" }
  };
});
</script>

<template>
  <div class="radar-wrap">
    <VChart class="radar-wrap__chart" :option="option" autoresize />
  </div>
</template>

<style scoped>
.radar-wrap {
  width: 100%;
  min-height: 260px;
}

.radar-wrap__chart {
  height: 280px;
  width: 100%;
}
</style>
