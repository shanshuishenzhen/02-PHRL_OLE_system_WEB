import { ref } from 'vue'
import { useFullscreen } from '@vueuse/core'
import { ElNotification } from 'element-plus'

// WebSocket连接状态
export const wsConnected = ref(false)
let socket: WebSocket | null = null
let screenshotInterval: number | null = null
const { isFullscreen, enter: enterFullscreen, exit: exitFullscreen } = useFullscreen()

// 初始化WebSocket连接
export function initWebSocket(examId: string) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const token = localStorage.getItem('token') || ''
  socket = new WebSocket(`${protocol}//${host}/ws/exam/${examId}/?token=${token}`)

  socket.onopen = () => {
    wsConnected.value = true
    console.log('WebSocket connected')
    
    // 进入全屏模式
    enterFullscreen()
    
    // 启动定时截屏上传
    startScreenshotUpload()
    
    // 监听全屏变化
    document.addEventListener('fullscreenchange', handleFullscreenChange)
  }

  socket.onclose = (event) => {
    wsConnected.value = false
    console.log('WebSocket disconnected:', event.code, event.reason)
    cleanupMonitoring()
    
    // 401错误表示token无效或过期
    if (event.code === 4003) {
      ElNotification.error({
        title: '认证失败',
        message: '登录已过期，请重新登录',
        duration: 0
      })
      // TODO: 触发重新登录逻辑
    }
  }

  socket.onerror = (error) => {
    console.error('WebSocket error:', error)
    cleanupMonitoring()
    
    // 401错误表示token无效或过期
    if (error instanceof CloseEvent && error.code === 4003) {
      ElNotification.error({
        title: '认证失败',
        message: '登录已过期，请重新登录',
        duration: 0
      })
      // TODO: 触发重新登录逻辑
    }
  }

  socket.onmessage = (event) => {
    try {
      const message = JSON.parse(event.data)
      handleWsMessage(message)
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error)
    }
  }
}

// 处理WebSocket消息
function handleWsMessage(message: any) {
  switch (message.type) {
    case WsMessageType.WARNING:
      handleWarningMessage(message)
      break
    case WsMessageType.COMMAND:
      handleCommandMessage(message)
      break
    case WsMessageType.NOTIFICATION:
      handleNotificationMessage(message)
      break
    default:
      console.log('Unknown message type:', message.type)
  }
}

// 处理警告消息
function handleWarningMessage(message: any) {
  ElNotification.warning({
    title: message.title || '考试警告',
    message: message.content || '检测到异常行为',
    duration: 0,
    showClose: true
  })
  
  // 记录违规行为
  sendWsMessage(WsMessageType.STUDENT_ACTION, {
    action: 'warning_received',
    details: message.content
  })
}

// 处理命令消息
function handleCommandMessage(message: any) {
  if (message.command === 'force_submit') {
    ElNotification.error({
      title: '强制提交',
      message: '监考员已强制提交您的考试',
      duration: 0,
      showClose: false
    })
    // TODO: 触发提交逻辑
  }
}

// 处理通知消息
function handleNotificationMessage(message: any) {
  ElNotification({
    title: message.title || '考试通知',
    message: message.content,
    type: message.notification_type || 'info',
    duration: 5000
  })
}

// 启动定时截屏上传
function startScreenshotUpload() {
  screenshotInterval = window.setInterval(async () => {
    try {
      const blob = await captureScreenshot()
      const reader = new FileReader()
      reader.onload = () => {
        sendWsMessage(WsMessageType.SCREENSHOT, {
          image: reader.result,
          timestamp: new Date().toISOString()
        })
      }
      reader.readAsDataURL(blob)
    } catch (error) {
      console.error('截屏上传失败:', error)
    }
  }, 30000) // 每30秒上传一次
}

// 捕获屏幕截图
async function captureScreenshot(): Promise<Blob> {
  // TODO: 实现实际截屏逻辑
  return new Blob()
}

// 处理全屏变化
function handleFullscreenChange() {
  if (!document.fullscreenElement) {
    sendWsMessage(WsMessageType.STUDENT_ACTION, {
      action: 'full_screen_exit',
      details: '考生退出全屏模式'
    })
    ElNotification.warning({
      title: '全屏警告',
      message: '请保持全屏模式进行考试',
      duration: 0
    })
    enterFullscreen()
  }
}

// 清理监控资源
function cleanupMonitoring() {
  if (screenshotInterval) {
    clearInterval(screenshotInterval)
    screenshotInterval = null
  }
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
}

// 发送消息
export function sendWsMessage(type: string, data: any) {
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ type, data }))
  }
}

// 关闭连接
export function closeWebSocket() {
  cleanupMonitoring()
  socket?.close()
}

// 消息类型定义
export enum WsMessageType {
  HEARTBEAT = 'heartbeat',
  SCREENSHOT = 'screenshot',
  WARNING = 'warning',
  COMMAND = 'command',
  NOTIFICATION = 'notification',
  STUDENT_ACTION = 'student_action'
}