// Notification system for leave applications
let notificationInterval

document.addEventListener("DOMContentLoaded", () => {
  console.log("Notifications script loaded")

  // Check for notifications immediately
  checkNotifications()

  // Check for notifications every 30 seconds
  notificationInterval = setInterval(checkNotifications, 30000)

  // Clear notifications when visiting leave pages
  clearNotificationsOnPageLoad()
})

function checkNotifications() {
  const currentPath = window.location.pathname
  console.log("Checking notifications for path:", currentPath)

  // Check admin leave notifications
  if (currentPath.includes("/admin/")) {
    fetch("/admin/get_leave_notification_count")
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        return response.json()
      })
      .then((data) => {
        console.log("Admin notification count:", data.count)
        updateNotificationBadge("admin-leave-badge", data.count)
      })
      .catch((error) => {
        console.error("Error checking admin notifications:", error)
      })
  }

  // Check employee leave notifications
  if (currentPath.includes("/employee/")) {
    fetch("/employee/get_leave_notification_count")
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        return response.json()
      })
      .then((data) => {
        console.log("Employee notification count:", data.count)
        updateNotificationBadge("employee-leave-badge", data.count)
      })
      .catch((error) => {
        console.error("Error checking employee notifications:", error)
      })
  }
}

function updateNotificationBadge(badgeId, count) {
  const badge = document.getElementById(badgeId)
  console.log(`Updating badge ${badgeId} with count ${count}`, badge)

  if (badge) {
    if (count > 0) {
      badge.textContent = count
      badge.style.display = "inline-flex"
      console.log(`Badge ${badgeId} shown with count ${count}`)
    } else {
      badge.style.display = "none"
      console.log(`Badge ${badgeId} hidden`)
    }
  } else {
    console.warn(`Badge element ${badgeId} not found`)
  }
}

function clearNotificationsOnPageLoad() {
  const currentPath = window.location.pathname

  if (currentPath.includes("/admin/leave_applications")) {
    setTimeout(() => {
      updateNotificationBadge("admin-leave-badge", 0)
    }, 1000)
  }

  if (currentPath.includes("/employee/apply_leave")) {
    setTimeout(() => {
      updateNotificationBadge("employee-leave-badge", 0)
    }, 1000)
  }
}

// Clean up interval when page unloads
window.addEventListener("beforeunload", () => {
  if (notificationInterval) {
    clearInterval(notificationInterval)
  }
})
