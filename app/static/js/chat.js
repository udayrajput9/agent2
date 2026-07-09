document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    const typingIndicator = document.getElementById('typing-indicator');

    if (!chatForm) return;

    // Scroll to bottom on load if there are messages
    chatMessages.scrollTop = chatMessages.scrollHeight;

    function appendMessage(content, role) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}`;
        
        // Handle basic markdown if needed or just text
        // For now, setting textContent is safer against XSS
        msgDiv.textContent = content;
        
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = chatInput.value.trim();
        if (!text) return;

        // Append user message
        appendMessage(text, 'user');
        chatInput.value = '';
        chatInput.disabled = true; // Disable input while waiting

        // Show typing indicator
        chatMessages.appendChild(typingIndicator);
        typingIndicator.classList.remove('hidden');
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            // Send request to the API
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();
            
            // Hide typing indicator
            typingIndicator.classList.add('hidden');
            chatInput.disabled = false;
            chatInput.focus();
            
            if (response.ok) {
                if (data.redirect_url) {
                    // If the trip plan is complete, the backend might redirect to the dashboard
                    window.location.href = data.redirect_url;
                } else if (data.messages && Array.isArray(data.messages)) {
                    // The backend returned a list of questions or messages
                    data.messages.forEach(msg => {
                        appendMessage(msg.content, msg.role || 'bot');
                    });
                } else if (data.reply) {
                     appendMessage(data.reply, 'bot');
                } else {
                     appendMessage("I'm working on your itinerary now! Please check your dashboard shortly.", 'bot');
                }
            } else {
                appendMessage(data.detail || "Sorry, I encountered an error while planning. Please try again.", 'bot');
            }
        } catch (error) {
            console.error('Chat error:', error);
            typingIndicator.classList.add('hidden');
            chatInput.disabled = false;
            chatInput.focus();
            appendMessage("Network error. Please check your connection and try again.", 'bot');
        }
    });
});
