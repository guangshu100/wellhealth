import request from './index'

export function login(username: string, password: string, captchaKey?: string, captchaCode?: string) {
  return request({
    url: '/users/login',
    method: 'POST',
    data: { username, password, captcha_key: captchaKey, captcha_code: captchaCode }
  })
}

export function wechatLogin(code: string) {
  return request({
    url: '/users/wechat-login',
    method: 'POST',
    data: { code }
  })
}

export function register(data: {
  username: string
  password: string
  name: string
  phone?: string
  email?: string
}) {
  return request({
    url: '/users/register',
    method: 'POST',
    data
  })
}

export function getUserInfo() {
  return request({
    url: '/users/me',
    method: 'GET'
  })
}

export function updateUserInfo(data: {
  name?: string
  avatar?: string
  phone?: string
  email?: string
}) {
  return request({
    url: '/users/me',
    method: 'PUT',
    data
  })
}

export function changePassword(oldPassword: string, newPassword: string) {
  return request({
    url: '/users/change-password',
    method: 'POST',
    data: { old_password: oldPassword, new_password: newPassword }
  })
}

export function logout() {
  return request({
    url: '/users/logout',
    method: 'POST'
  })
}

export function getRoles() {
  return request({
    url: '/users/roles',
    method: 'GET'
  })
}

export function getPermissions() {
  return request({
    url: '/users/permissions',
    method: 'GET'
  })
}

export function emailLogin(email: string, code: string, captchaKey?: string, captchaCode?: string) {
  return request({
    url: '/users/email-login',
    method: 'POST',
    data: { email, code, captcha_key: captchaKey, captcha_code: captchaCode }
  })
}

export function sendEmailCode(email: string, purpose: string = 'register') {
  return request({
    url: '/users/email/code',
    method: 'POST',
    data: { email, purpose }
  })
}

export function verifyEmailCode(email: string, code: string) {
  return request({
    url: '/users/email/verify',
    method: 'POST',
    data: { email, code }
  })
}

export function registerWithEmail(data: {
  email: string
  code: string
  password: string
  name: string
  phone?: string
}) {
  return request({
    url: '/users/register/email',
    method: 'POST',
    data
  })
}

export function resetPassword(email: string, code: string, newPassword: string) {
  return request({
    url: '/users/reset-password',
    method: 'POST',
    data: { email, code, new_password: newPassword }
  })
}
