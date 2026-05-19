import request from './index'

export function getCaptcha() {
  return request({
    url: '/captcha/captcha',
    method: 'GET'
  })
}
