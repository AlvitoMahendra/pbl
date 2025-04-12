document.addEventListener("DOMContentLoaded", function () {
  // Variabel untuk menyimpan username penerima pesan yang aktif
  let activeReceiver = null;
  const currentUser = document
    .getElementById("current-user-data")
    .getAttribute("data-username");

  // Inisiasi koneksi Socket.IO
  const socket = io();

  // DOM Elements
  const contactItems = document.querySelectorAll(".contact-item");
  const messageList = document.getElementById("message-list");
  const messageInput = document.getElementById("message-input");
  const sendButton = document.getElementById("send-button");
  const selectContactPlaceholder = document.getElementById(
    "select-contact-placeholder"
  );
  const messageInputContainer = document.getElementById(
    "message-input-container"
  );
  const activeContactName = document.getElementById("active-contact-name");
  const activeContactStatus = document.getElementById("active-contact-status");

  // Event listener untuk item kontak
  contactItems.forEach((item) => {
    item.addEventListener("click", function () {
      const username = this.getAttribute("data-username");

      // Tandai kontak sebagai aktif
      contactItems.forEach((c) => c.classList.remove("active"));
      this.classList.add("active");

      // Simpan penerima yang aktif
      activeReceiver = username;

      // Update header chat
      activeContactName.textContent = username;
      const statusElement = this.querySelector(".bg-success, .bg-danger");
      activeContactStatus.className = statusElement.className;

      // Tampilkan container input pesan
      messageInputContainer.style.display = "flex";

      // Sembunyikan placeholder dan tampilkan daftar pesan
      selectContactPlaceholder.classList.add("d-none");
      messageList.classList.remove("d-none");

      // Ambil riwayat pesan
      fetchMessages(username);
    });
  });

  // Fungsi untuk mengambil riwayat pesan
  function fetchMessages(receiver) {
    fetch(`/get_messages/${receiver}`)
      .then((response) => response.json())
      .then((messages) => {
        // Bersihkan daftar pesan
        messageList.innerHTML = "";

        // Tambahkan pesan ke daftar
        messages.forEach((message) => {
          addMessageToList(message);
        });

        // Scroll ke pesan terbaru
        scrollToBottom();
      })
      .catch((error) => console.error("Error fetching messages:", error));
  }

  // Fungsi untuk menambahkan pesan ke daftar
  function addMessageToList(message) {
    const isMe = message.sender === currentUser;
    const messageElement = document.createElement("div");
    messageElement.className = isMe ? "owner-message" : "guest-message";

    messageElement.innerHTML = `
            <div class="${isMe ? "self-message" : "other-message"}" >
                <div class="message-content">
                    <div class="message-text">
                        <p>${message.message}</p>
                    </div>
                </div>
                <div class="message-meta" style="z-index:-1;">
                    <span class="fs-10 text-muted" style="color:black !important; font-weight: 700;">${message.timestamp}</span>
                </div>
            </div>
        `;

    messageList.appendChild(messageElement);
  }

  // Fungsi untuk scroll ke pesan terbaru
  function scrollToBottom() {
    const chatContainer = document.querySelector(".conversation-wrapper-inner");
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }

  // Event listener untuk tombol kirim
  sendButton.addEventListener("click", sendMessage);

  // Event listener untuk input pesan (kirim dengan Enter)
  messageInput.addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
      event.preventDefault();
      sendMessage();
    }
  });

  // Fungsi untuk mengirim pesan
  function sendMessage() {
    const message = messageInput.value.trim();

    if (!message || !activeReceiver) {
      return;
    }

    // Kirim pesan melalui Socket.IO
    socket.emit("send_message", {
      receiver: activeReceiver,
      message: message,
    });

    // Bersihkan input pesan
    messageInput.value = "";
  }

  // Socket.IO event handlers
  socket.on("connect", function () {
    console.log("Connected to server");
  });

  socket.on("receive_message", function (message) {
    if (
      (message.sender === currentUser && message.receiver === activeReceiver) ||
      (message.sender === activeReceiver && message.receiver === currentUser)
    ) {
      // Tambahkan pesan ke daftar jika terkait dengan percakapan aktif
      addMessageToList(message);
      scrollToBottom();
    }
  });

  socket.on("user_status", function (data) {
    // Update status pengguna di daftar kontak
    const contactItem = document.querySelector(
      `.contact-item[data-username="${data.username}"]`
    );
    if (contactItem) {
      const statusDot = contactItem.querySelector(".rounded-circle");
      const statusText = contactItem.querySelector(".status-text");

      if (data.status === "online") {
        statusDot.classList.remove("bg-danger");
        statusDot.classList.add("bg-success");
        statusText.textContent = "online";
      } else {
        statusDot.classList.remove("bg-success");
        statusDot.classList.add("bg-danger");
        statusText.textContent = "offline";
      }

      // Update status kontak aktif jika perlu
      if (data.username === activeReceiver) {
        activeContactStatus.className = statusDot.className;
      }
    }
  });
});
