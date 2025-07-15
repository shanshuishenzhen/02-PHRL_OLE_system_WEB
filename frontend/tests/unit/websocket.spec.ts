import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { initWebSocket, closeWebSocket, sendWsMessage, WsMessageType } from '../../src/api/websocket'
import { ElNotification } from 'element-plus'

// Mock WebSocket
class MockWebSocket {
  static instances: MockWebSocket[] = []
  onopen: (() => void) = () => {}
  onclose: (event: { code: number }) => void = () => {}
  onerror: ((error: any) => void) = () => {}
  onmessage: (event: { data: string }) => void = () => {}
  readyState = 0

  constructor() {
    MockWebSocket.instances.push(this)
    setTimeout(() => {
      this.readyState = 1
      this.onopen()
    }, 10)
  }

  send(data: string) {
    console.log('Mock WebSocket send:', data)
  }

  close(code?: number) {
    this.readyState = 3
    this.onclose({ code: code || 1000 })
  }
}

// Mock element-plus notification
vi.mock('element-plus', () => ({
  ElNotification: {
    warning: vi.fn(),
    error: vi.fn(),
    info: vi.fn()
  }
}))

describe('WebSocket防作弊功能测试', () => {
  beforeEach(() => {
    window.WebSocket = MockWebSocket as any
  })

  afterEach(() => {
    closeWebSocket()
    MockWebSocket.instances = []
    vi.clearAllMocks()
  })

  it('应正确初始化WebSocket连接', async () => {
    initWebSocket('exam123')
    await new Promise(resolve => setTimeout(resolve, 20))
    
    expect(MockWebSocket.instances.length).toBe(1)
    expect(ElNotification.warning).not.toHaveBeenCalled()
  })

  it('应处理全屏退出警告', async () => {
    initWebSocket('exam123')
    await new Promise(resolve => setTimeout(resolve, 20))
    
    // 模拟退出全屏
    document.dispatchEvent(new Event('fullscreenchange'))
    expect(ElNotification.warning).toHaveBeenCalled()
  })

  it('应发送截屏数据', async () => {
    initWebSocket('exam123')
    await new Promise(resolve => setTimeout(resolve, 20))
    
    const mockSend = vi.spyOn(MockWebSocket.instances[0], 'send')
    sendWsMessage(WsMessageType.SCREENSHOT, { image: 'test' })
    expect(mockSend).toHaveBeenCalled()
  })

  it('应处理认证失败', async () => {
    initWebSocket('exam123')
    await new Promise(resolve => setTimeout(resolve, 20))
    
    MockWebSocket.instances[0].onclose({ code: 4003 })
    expect(ElNotification.error).toHaveBeenCalled()
  })
})