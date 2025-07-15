<template>
  <div id="app">
    <el-config-provider :locale="zhCn">
      <router-view v-slot="{ Component }">
        <template v-if="Component">
          <suspense>
            <component :is="Component" />
            <template #fallback>
              <div class="loading-container">
                <el-icon class="is-loading" size="30">
                  <Loading />
                </el-icon>
                <span>加载中...</span>
              </div>
            </template>
          </suspense>
        </template>
      </router-view>
    </el-config-provider>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import { ElConfigProvider, ElIcon } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { Loading } from '@element-plus/icons-vue'

export default defineComponent({
  name: 'App',
  components: {
    ElConfigProvider,
    ElIcon,
    Loading
  },
  setup() {
    return {
      zhCn
    }
  }
})
</script>

<style>
#app {
  height: 100vh;
  font-family: Arial, sans-serif;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  gap: 10px;
}
</style>