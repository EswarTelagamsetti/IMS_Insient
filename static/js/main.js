// Main JavaScript functionality
document.addEventListener("DOMContentLoaded", () => {
  // Close alert messages
  const closeButtons = document.querySelectorAll(".close-alert")
  closeButtons.forEach((button) => {
    button.addEventListener("click", function () {
      this.parentElement.style.display = "none"
    })
  })

  // Auto-hide alerts after 5 seconds
  const alerts = document.querySelectorAll(".alert")
  alerts.forEach((alert) => {
    setTimeout(() => {
      alert.style.opacity = "0"
      setTimeout(() => {
        alert.style.display = "none"
      }, 300)
    }, 5000)
  })

  // Active sidebar link
  const currentPath = window.location.pathname
  const sidebarLinks = document.querySelectorAll(".sidebar-menu a")
  sidebarLinks.forEach((link) => {
    if (link.getAttribute("href") === currentPath) {
      link.classList.add("active")
    }
  })

  // Modal functionality
  const modals = document.querySelectorAll(".modal")
  const modalTriggers = document.querySelectorAll("[data-modal]")
  const closeButtonModal = document.querySelectorAll(".close")

  modalTriggers.forEach((trigger) => {
    trigger.addEventListener("click", function (e) {
      e.preventDefault()
      const modalId = this.getAttribute("data-modal")
      const modal = document.getElementById(modalId)
      if (modal) {
        modal.style.display = "block"
      }
    })
  })

  closeButtonModal.forEach((button) => {
    button.addEventListener("click", function () {
      const modal = this.closest(".modal")
      if (modal) {
        modal.style.display = "none"
      }
    })
  })

  // Close modal when clicking outside
  modals.forEach((modal) => {
    modal.addEventListener("click", function (e) {
      if (e.target === this) {
        this.style.display = "none"
      }
    })
  })

  // Search functionality
  const searchInputs = document.querySelectorAll(".search-input")
  searchInputs.forEach((input) => {
    input.addEventListener("input", function () {
      const searchTerm = this.value.toLowerCase()
      const searchableItems = document.querySelectorAll(".searchable")

      searchableItems.forEach((item) => {
        const text = item.textContent.toLowerCase()
        if (text.includes(searchTerm)) {
          item.style.display = ""
        } else {
          item.style.display = "none"
        }
      })
    })
  })

  // Form validation
  const forms = document.querySelectorAll("form")
  forms.forEach((form) => {
    form.addEventListener("submit", (e) => {
      const requiredFields = form.querySelectorAll("[required]")
      let isValid = true

      requiredFields.forEach((field) => {
        if (!field.value.trim()) {
          isValid = false
          field.style.borderColor = "#dc3545"
        } else {
          field.style.borderColor = "#e9ecef"
        }
      })

      if (!isValid) {
        e.preventDefault()
        showAlert("Please fill in all required fields.", "error")
      }
    })
  })

  // Confirmation dialogs
  const confirmButtons = document.querySelectorAll(".confirm-action")
  confirmButtons.forEach((button) => {
    button.addEventListener("click", function (e) {
      const message = this.getAttribute("data-confirm") || "Are you sure?"
      if (!confirm(message)) {
        e.preventDefault()
      }
    })
  })
})

// Utility functions
function showAlert(message, type = "info") {
  const alertContainer = document.querySelector(".flash-messages") || createAlertContainer()

  const alert = document.createElement("div")
  alert.className = `alert alert-${type}`
  alert.innerHTML = `
        ${message}
        <button type="button" class="close-alert">&times;</button>
    `

  alertContainer.appendChild(alert)

  // Add close functionality
  const closeBtn = alert.querySelector(".close-alert")
  closeBtn.addEventListener("click", () => {
    alert.remove()
  })

  // Auto-remove after 5 seconds
  setTimeout(() => {
    if (alert.parentNode) {
      alert.remove()
    }
  }, 5000)
}

function createAlertContainer() {
  const container = document.createElement("div")
  container.className = "flash-messages"
  document.body.appendChild(container)
  return container
}

function formatDate(dateString) {
  const date = new Date(dateString)
  return date.toLocaleDateString() + " " + date.toLocaleTimeString()
}

function formatRelativeTime(dateString) {
  const date = new Date(dateString)
  const now = new Date()
  const diffInSeconds = Math.floor((now - date) / 1000)

  if (diffInSeconds < 60) {
    return "Just now"
  } else if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60)
    return `${minutes} minute${minutes > 1 ? "s" : ""} ago`
  } else if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600)
    return `${hours} hour${hours > 1 ? "s" : ""} ago`
  } else {
    const days = Math.floor(diffInSeconds / 86400)
    return `${days} day${days > 1 ? "s" : ""} ago`
  }
}

// AJAX helper function
function makeRequest(url, method = "GET", data = null) {
  return fetch(url, {
    method: method,
    headers: {
      "Content-Type": "application/json",
      "X-Requested-With": "XMLHttpRequest",
    },
    body: data ? JSON.stringify(data) : null,
  }).then((response) => {
    if (!response.ok) {
      throw new Error("Network response was not ok")
    }
    return response.json()
  })
}
