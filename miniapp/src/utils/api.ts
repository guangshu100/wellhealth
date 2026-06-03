const BASE_URL = 'http://localhost:8000/api/v1'

interface RequestOptions {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: any
  header?: Record<string, string>
  contentType?: string
}

function getToken(): string {
  return uni.getStorageSync('token') || ''
}

function getTokenType(): string {
  return uni.getStorageSync('tokenType') || 'Bearer'
}

function request<T = any>(options: RequestOptions): Promise<T> {
  return new Promise((resolve, reject) => {
    const token = getToken()
    const tokenType = getTokenType()
    const contentType = options.contentType || 'application/json'
    const header: Record<string, string> = {
      'Content-Type': contentType,
      ...options.header,
    }
    if (token) {
      header['Authorization'] = `${tokenType} ${token}`
    }

    uni.request({
      url: `${BASE_URL}${options.url}`,
      method: options.method || 'GET',
      data: options.data,
      header,
      success: (res) => {
        if (res.statusCode === 200) {
          resolve(res.data as T)
        } else if (res.statusCode === 401) {
          uni.removeStorageSync('token')
          uni.removeStorageSync('tokenType')
          uni.removeStorageSync('userInfo')
          uni.reLaunch({ url: '/pages/login/index' })
          reject(new Error('未授权，请重新登录'))
        } else {
          reject(new Error(`请求失败: ${res.statusCode}`))
        }
      },
      fail: (err) => {
        reject(new Error(err.errMsg || '网络请求失败'))
      },
    })
  })
}

export const api = {
  get<T = any>(url: string, data?: any): Promise<T> {
    return request<T>({ url, method: 'GET', data })
  },
  post<T = any>(url: string, data?: any, contentType?: string): Promise<T> {
    return request<T>({ url, method: 'POST', data, contentType })
  },
  put<T = any>(url: string, data?: any): Promise<T> {
    return request<T>({ url, method: 'PUT', data })
  },
  delete<T = any>(url: string, data?: any): Promise<T> {
    return request<T>({ url, method: 'DELETE', data })
  },
  postForm<T = any>(url: string, data?: Record<string, string>): Promise<T> {
    const params = new URLSearchParams(data).toString()
    return request<T>({
      url,
      method: 'POST',
      data: params,
      contentType: 'application/x-www-form-urlencoded',
    })
  },
}

export default api
