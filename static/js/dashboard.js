// Dashboard specific functionality
document.addEventListener("DOMContentLoaded", () => {
  // Update real-time data
  updateDashboardData()

  // Set interval to update data every 30 seconds
  setInterval(updateDashboardData, 30000)

  // Initialize charts if needed
  initializeCharts()

  // Update experience every hour
  setInterval(updateExperience, 3600000)
})

function updateDashboardData() {
  // Update availability status
  updateAvailabilityStatus()

  // Update recent activities
  updateRecentActivities()

  // Update statistics
  updateStatistics()
}

function updateAvailabilityStatus() {
  const availabilityIndicator = document.querySelector(".availability-status")
  if (availabilityIndicator) {
    fetch("/api/availability-status")
      .then((response) => response.json())
      .then((data) => {
        availabilityIndicator.textContent = data.is_available ? "Available" : "Unavailable"
        availabilityIndicator.className = `availability-status ${data.is_available ? "available" : "unavailable"}`
      })
      .catch((error) => console.error("Error updating availability:", error))
  }
}

function updateRecentActivities() {
  const activitiesContainer = document.querySelector(".recent-activities")
  if (activitiesContainer) {
    fetch("/api/recent-activities")
      .then((response) => response.json())
      .then((data) => {
        activitiesContainer.innerHTML = ""
        data.activities.forEach((activity) => {
          const activityElement = createActivityElement(activity)
          activitiesContainer.appendChild(activityElement)
        })
      })
      .catch((error) => console.error("Error updating activities:", error))
  }
}

function updateStatistics() {
  const statElements = document.querySelectorAll(".stat-number")
  statElements.forEach((element) => {
    const statType = element.getAttribute("data-stat")
    if (statType) {
      fetch(`/api/stats/${statType}`)
        .then((response) => response.json())
        .then((data) => {
          element.textContent = data.value
        })
        .catch((error) => console.error("Error updating stats:", error))
    }
  })
}

function createActivityElement(activity) {
  const div = document.createElement("div")
  div.className = "activity-item"
  div.innerHTML = `
        <div class="activity-icon ${activity.type}">
            <i class="fas ${getActivityIcon(activity.type)}"></i>
        </div>
        <div class="activity-content">
            <div class="activity-title">${activity.title}</div>
            <div class="activity-time">${formatRelativeTime(activity.created_at)}</div>
        </div>
    `
  return div
}

function getActivityIcon(type) {
  const icons = {
    ticket_created: "fa-plus",
    ticket_completed: "fa-check",
    availability_changed: "fa-toggle-on",
    profile_updated: "fa-user-edit",
  }
  return icons[type] || "fa-info"
}

function initializeCharts() {
  // Initialize any charts or graphs here
  // This would typically use a library like Chart.js
}

// Availability toggle functionality
function toggleAvailability() {
  const toggle = document.querySelector("#availability-toggle")
  if (toggle) {
    const isAvailable = toggle.checked

    fetch("/employee/availability", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: `is_available=${isAvailable ? "on" : "off"}`,
    })
      .then((response) => {
        if (response.ok) {
          showAlert(`Availability ${isAvailable ? "enabled" : "disabled"}`, "success")
        } else {
          throw new Error("Failed to update availability")
        }
      })
      .catch((error) => {
        console.error("Error:", error)
        showAlert("Failed to update availability", "error")
        // Revert toggle state
        toggle.checked = !isAvailable
      })
  }
}

// Profile experience update
function updateExperience() {
  const experienceElement = document.querySelector(".experience-display")
  if (experienceElement) {
    const startDate = experienceElement.getAttribute("data-start-date")
    if (startDate) {
      const experience = calculateExperience(startDate)
      experienceElement.textContent = experience
    }
  }
}

function calculateExperience(startDateString) {
  const startDate = new Date(startDateString)
  const now = new Date()
  const diffInDays = Math.floor((now - startDate) / (1000 * 60 * 60 * 24))

  if (diffInDays < 30) {
    return `${diffInDays} days`
  } else if (diffInDays < 365) {
    const months = Math.floor(diffInDays / 30)
    const remainingDays = diffInDays % 30
    if (remainingDays > 0) {
      return `${months} months, ${remainingDays} days`
    } else {
      return `${months} months`
    }
  } else {
    const years = Math.floor(diffInDays / 365)
    const remainingDays = diffInDays % 365
    const months = Math.floor(remainingDays / 30)
    if (months > 0) {
      return `${years} years, ${months} months`
    } else {
      return `${years} years`
    }
  }
}

// Declare formatRelativeTime function
function formatRelativeTime(date) {
  // Implement formatRelativeTime logic here
  return new Date(date).toLocaleString()
}

// Declare showAlert function
function showAlert(message, type) {
  // Implement showAlert logic here
  alert(`${type.toUpperCase()}: ${message}`)
}
