// Ticket management functionality
document.addEventListener("DOMContentLoaded", () => {
  initializeTicketFunctionality()
})

function initializeTicketFunctionality() {
  // Initialize user search for ticket assignment
  initializeUserSearch()

  // Initialize ticket filters
  initializeTicketFilters()

  // Initialize ticket actions
  initializeTicketActions()
}

function initializeUserSearch() {
  const userSearchInput = document.getElementById("user-search")
  const userList = document.getElementById("user-list")
  const selectedUserInput = document.getElementById("assigned_to")

  if (userSearchInput && userList) {
    userSearchInput.addEventListener("input", function () {
      const searchTerm = this.value.toLowerCase()

      if (searchTerm.length < 2) {
        userList.innerHTML = ""
        return
      }

      // Get filter values
      const branchId = document.getElementById("branch-filter")?.value
      const workType = document.getElementById("work-type-filter")?.value
      const role = document.getElementById("role-filter")?.value
      const availableOnly = document.getElementById("available-only")?.checked

      // Build query parameters
      const params = new URLSearchParams()
      if (branchId) params.append("branch_id", branchId)
      if (workType) params.append("work_type", workType)
      if (role) params.append("role", role)
      if (availableOnly) params.append("available_only", "true")

      // Fetch users based on search and filters
      let endpoint = "/admin/get_users"
      if (window.location.pathname.includes("/employee/")) {
        endpoint = "/employee/get_available_employees"
      }

      fetch(`${endpoint}?${params.toString()}`)
        .then((response) => response.json())
        .then((users) => {
          displayUsers(
            users.filter(
              (user) => user.name.toLowerCase().includes(searchTerm) || user.email.toLowerCase().includes(searchTerm),
            ),
          )
        })
        .catch((error) => {
          console.error("Error fetching users:", error)
          userList.innerHTML = '<div class="error">Error loading users</div>'
        })
    })
  }
}

function displayUsers(users) {
  const userList = document.getElementById("user-list")

  if (users.length === 0) {
    userList.innerHTML = '<div class="empty-state">No users found</div>'
    return
  }

  userList.innerHTML = users
    .map(
      (user) => `
        <div class="user-item" onclick="selectUser(${user.id}, '${user.name}', '${user.email}')">
            <div class="user-avatar">${user.name.charAt(0).toUpperCase()}</div>
            <div class="user-info">
                <h4>${user.name}</h4>
                <p>${user.email} - ${user.role}</p>
            </div>
            <div class="status-indicator ${user.is_available ? "available" : "unavailable"}"></div>
        </div>
    `,
    )
    .join("")
}

function selectUser(userId, userName, userEmail) {
  const selectedUserInput = document.getElementById("assigned_to")
  const userSearchInput = document.getElementById("user-search")
  const userList = document.getElementById("user-list")

  if (selectedUserInput) {
    selectedUserInput.value = userId
  }

  if (userSearchInput) {
    userSearchInput.value = `${userName} (${userEmail})`
  }

  if (userList) {
    userList.innerHTML = ""
  }
}

function initializeTicketFilters() {
  const filterInputs = document.querySelectorAll(".ticket-filter")

  filterInputs.forEach((input) => {
    input.addEventListener("change", () => {
      filterTickets()
    })
  })
}

function filterTickets() {
  const statusFilter = document.getElementById("status-filter")?.value
  const dateFilter = document.getElementById("date-filter")?.value
  const assignedByFilter = document.getElementById("assigned-by-filter")?.value

  const tickets = document.querySelectorAll(".ticket-card")

  tickets.forEach((ticket) => {
    let show = true

    // Status filter
    if (statusFilter && statusFilter !== "all") {
      const ticketStatus = ticket.getAttribute("data-status")
      if (ticketStatus !== statusFilter) {
        show = false
      }
    }

    // Date filter
    if (dateFilter && dateFilter !== "all") {
      const ticketDate = new Date(ticket.getAttribute("data-created"))
      const now = new Date()
      let showByDate = false

      switch (dateFilter) {
        case "today":
          showByDate = ticketDate.toDateString() === now.toDateString()
          break
        case "week":
          const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
          showByDate = ticketDate >= weekAgo
          break
        case "month":
          const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
          showByDate = ticketDate >= monthAgo
          break
      }

      if (!showByDate) {
        show = false
      }
    }

    // Assigned by filter
    if (assignedByFilter && assignedByFilter !== "all") {
      const assignedBy = ticket.getAttribute("data-assigned-by")
      if (assignedBy !== assignedByFilter) {
        show = false
      }
    }

    ticket.style.display = show ? "block" : "none"
  })
}

function initializeTicketActions() {
  // Complete ticket buttons
  const completeButtons = document.querySelectorAll(".complete-ticket")
  completeButtons.forEach((button) => {
    button.addEventListener("click", function (e) {
      e.preventDefault()
      const ticketId = this.getAttribute("data-ticket-id")
      completeTicket(ticketId)
    })
  })

  // View ticket details
  const viewButtons = document.querySelectorAll(".view-ticket")
  viewButtons.forEach((button) => {
    button.addEventListener("click", function (e) {
      e.preventDefault()
      const ticketId = this.getAttribute("data-ticket-id")
      viewTicketDetails(ticketId)
    })
  })
}

function completeTicket(ticketId) {
  if (!confirm("Are you sure you want to mark this ticket as completed?")) {
    return
  }

  const endpoint = window.location.pathname.includes("/intern/")
    ? `/intern/complete_work/${ticketId}`
    : `/employee/complete_ticket/${ticketId}`

  fetch(endpoint, {
    method: "GET",
  })
    .then((response) => {
      if (response.ok) {
        showAlert("Ticket marked as completed!", "success")
        // Remove ticket from current view or update its status
        const ticketCard = document.querySelector(`[data-ticket-id="${ticketId}"]`).closest(".ticket-card")
        if (ticketCard) {
          ticketCard.style.opacity = "0.5"
          setTimeout(() => {
            ticketCard.remove()
          }, 1000)
        }
      } else {
        throw new Error("Failed to complete ticket")
      }
    })
    .catch((error) => {
      console.error("Error:", error)
      showAlert("Failed to complete ticket", "error")
    })
}

function viewTicketDetails(ticketId) {
  // This would open a modal with full ticket details
  const modal = document.getElementById("ticket-details-modal")
  if (modal) {
    // Fetch ticket details and populate modal
    fetch(`/api/ticket/${ticketId}`)
      .then((response) => response.json())
      .then((ticket) => {
        populateTicketModal(ticket)
        modal.style.display = "block"
      })
      .catch((error) => {
        console.error("Error fetching ticket details:", error)
        showAlert("Failed to load ticket details", "error")
      })
  }
}

function populateTicketModal(ticket) {
  const modal = document.getElementById("ticket-details-modal")

  modal.querySelector(".modal-title").textContent = ticket.title
  modal.querySelector(".ticket-description").textContent = ticket.description
  modal.querySelector(".ticket-raised-by").textContent = ticket.raised_by_name
  modal.querySelector(".ticket-created-at").textContent = formatDate(ticket.created_at)

  if (ticket.completed_at) {
    modal.querySelector(".ticket-completed-at").textContent = formatDate(ticket.completed_at)
    modal.querySelector(".completion-info").style.display = "block"
  } else {
    modal.querySelector(".completion-info").style.display = "none"
  }
}

// Auto-refresh tickets every 2 minutes
setInterval(() => {
  if (window.location.pathname.includes("/tickets") || window.location.pathname.includes("/works")) {
    location.reload()
  }
}, 120000)

// Declare showAlert function
function showAlert(message, type) {
  const alertContainer = document.createElement("div")
  alertContainer.className = `alert ${type}`
  alertContainer.textContent = message
  document.body.appendChild(alertContainer)

  setTimeout(() => {
    document.body.removeChild(alertContainer)
  }, 3000)
}

// Declare formatDate function
function formatDate(dateString) {
  const date = new Date(dateString)
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  })
}
