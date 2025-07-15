export const markPaper = async (file: File) => {
  const formData = new FormData()
  formData.append('answer_sheet', file)
  return request({
    url: '/marking/auto-score',
    method: 'POST',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}