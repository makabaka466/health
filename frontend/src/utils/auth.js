export function clearAuthStorage() {
  localStorage.removeItem('token')
  localStorage.removeItem('adminToken')
  localStorage.removeItem('username')
  localStorage.removeItem('adminUsername')
  localStorage.removeItem('userRole')
}

export function redirectToLogin() {
  window.location.replace('/login')
}
