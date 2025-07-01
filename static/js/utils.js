// Utility functions for the application

// Date formatting utilities
function formatDate(dateString) {
  const date = new Date(dateString)
  const options = {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }
  return date.toLocaleDateString("en-US", options)
}

function formatRelativeTime(dateString) {
  const date = new Date(dateString)
  const now = new Date()
  const diffInSeconds = Math.floor((now - date) / 1000)

  const intervals = {
    year: 31536000,
    month: 2592000,
    week: 604800,
    day: 86400,
    hour: 3600,
    minute: 60,
  }

  for (const [unit, seconds] of Object.entries(intervals)) {
    const interval = Math.floor(diffInSeconds / seconds)
    if (interval >= 1) {
      return `${interval} ${unit}${interval > 1 ? "s" : ""} ago`
    }
  }

  return "Just now"
}

// Form validation utilities
function validateEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

function validatePassword(password) {
  // At least 6 characters
  return password.length >= 6
}

function validateForm(form) {
  const errors = []
  const requiredFields = form.querySelectorAll("[required]")

  requiredFields.forEach((field) => {
    if (!field.value.trim()) {
      errors.push(`${field.name || field.id} is required`)
      field.classList.add("error")
    } else {
      field.classList.remove("error")
    }

    // Specific validations
    if (field.type === "email" && field.value && !validateEmail(field.value)) {
      errors.push("Please enter a valid email address")
      field.classList.add("error")
    }

    if (field.type === "password" && field.value && !validatePassword(field.value)) {
      errors.push("Password must be at least 6 characters long")
      field.classList.add("error")
    }
  })

  // Password confirmation
  const password = form.querySelector('input[name="new_password"]')
  const confirmPassword = form.querySelector('input[name="confirm_password"]')

  if (password && confirmPassword && password.value !== confirmPassword.value) {
    errors.push("Passwords do not match")
    confirmPassword.classList.add("error")
  }

  return errors
}

// Local storage utilities
function saveToLocalStorage(key, data) {
  try {
    localStorage.setItem(key, JSON.stringify(data))
    return true
  } catch (error) {
    console.error("Error saving to localStorage:", error)
    return false
  }
}

function getFromLocalStorage(key) {
  try {
    const data = localStorage.getItem(key)
    return data ? JSON.parse(data) : null
  } catch (error) {
    console.error("Error reading from localStorage:", error)
    return null
  }
}

function removeFromLocalStorage(key) {
  try {
    localStorage.removeItem(key)
    return true
  } catch (error) {
    console.error("Error removing from localStorage:", error)
    return false
  }
}

// API utilities
function makeApiRequest(url, options = {}) {
  const defaultOptions = {
    headers: {
      "Content-Type": "application/json",
      "X-Requested-With": "XMLHttpRequest",
    },
  }

  const mergedOptions = { ...defaultOptions, ...options }

  return fetch(url, mergedOptions).then((response) => {
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return response.json()
  })
}

// UI utilities
function showLoading(element) {
  const originalContent = element.innerHTML
  element.innerHTML = '<div class="loading"><div class="spinner"></div></div>'
  element.setAttribute("data-original-content", originalContent)
  element.disabled = true
}

function hideLoading(element) {
  const originalContent = element.getAttribute("data-original-content")
  if (originalContent) {
    element.innerHTML = originalContent
    element.removeAttribute("data-original-content")
  }
  element.disabled = false
}

function debounce(func, wait) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

function throttle(func, limit) {
  let inThrottle
  return function () {
    const args = arguments
    
    if (!inThrottle) {
      func.apply(this, args)
      inThrottle = true
      setTimeout(() => (inThrottle = false), limit)
    }
  }
}

// Export utilities for use in other scripts
window.utils = {
  formatDate,
  formatRelativeTime,
  validateEmail,
  validatePassword,
  validateForm,
  saveToLocalStorage,
  getFromLocalStorage,
  removeFromLocalStorage,
  makeApiRequest,
  showLoading,
  hideLoading,
  debounce,
  throttle,
}
