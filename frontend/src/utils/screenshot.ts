import html2canvas from 'html2canvas'

/**
 * 捕获整个页面截图
 */
export async function captureFullPage(): Promise<Blob> {
  const canvas = await html2canvas(document.body, {
    useCORS: true,
    allowTaint: true,
    scale: 0.5, // 降低分辨率减少大小
    logging: false,
    ignoreElements: (element) => {
      // 忽略隐藏元素
      return element.style.display === 'none' || 
             element.style.visibility === 'hidden'
    }
  })
  
  return new Promise((resolve) => {
    canvas.toBlob((blob) => {
      if (blob) {
        resolve(blob)
      } else {
        throw new Error('Failed to convert canvas to blob')
      }
    }, 'image/jpeg', 0.7) // JPEG格式，70%质量
  })
}

/**
 * 捕获考试内容区域截图
 * @param selector 考试内容区域选择器
 */
export async function captureExamArea(selector: string): Promise<Blob> {
  const element = document.querySelector(selector)
  if (!element) {
    throw new Error(`Element not found with selector: ${selector}`)
  }

  const canvas = await html2canvas(element as HTMLElement, {
    useCORS: true,
    allowTaint: true,
    scale: 0.8,
    logging: false
  })

  return new Promise((resolve) => {
    canvas.toBlob((blob) => {
      if (blob) {
        resolve(blob)
      } else {
        throw new Error('Failed to convert canvas to blob')
      }
    }, 'image/jpeg', 0.8)
  })
}