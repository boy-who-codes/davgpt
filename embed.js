(function() {
    // Create floating chat bubble
    const bubble = document.createElement('div');
    bubble.id = 'davgpt-bubble';
    bubble.innerHTML = '💬';
    bubble.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: linear-gradient(135deg, #007AFF, #0056CC);
        color: white;
        font-size: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 4px 20px rgba(0, 122, 255, 0.3);
        z-index: 9999;
        transition: all 0.3s ease;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    `;

    // Hover effect
    bubble.addEventListener('mouseenter', () => {
        bubble.style.transform = 'scale(1.1)';
        bubble.style.boxShadow = '0 6px 25px rgba(0, 122, 255, 0.4)';
    });

    bubble.addEventListener('mouseleave', () => {
        bubble.style.transform = 'scale(1)';
        bubble.style.boxShadow = '0 4px 20px rgba(0, 122, 255, 0.3)';
    });

    // Create chat iframe
    let chatFrame = null;
    let isOpen = false;

    bubble.addEventListener('click', () => {
        if (!isOpen) {
            chatFrame = document.createElement('iframe');
            chatFrame.src = 'http://localhost:5000'; // Replace with your domain
            chatFrame.style.cssText = `
                position: fixed;
                bottom: 90px;
                right: 20px;
                width: 400px;
                height: 600px;
                border: none;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
                z-index: 9998;
                opacity: 0;
                transform: translateY(20px);
                transition: all 0.3s ease;
            `;
            
            document.body.appendChild(chatFrame);
            
            // Animate in
            setTimeout(() => {
                chatFrame.style.opacity = '1';
                chatFrame.style.transform = 'translateY(0)';
            }, 10);
            
            bubble.innerHTML = '✕';
            isOpen = true;
        } else {
            // Animate out
            chatFrame.style.opacity = '0';
            chatFrame.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                if (chatFrame) {
                    document.body.removeChild(chatFrame);
                    chatFrame = null;
                }
            }, 300);
            
            bubble.innerHTML = '💬';
            isOpen = false;
        }
    });

    document.body.appendChild(bubble);
})();
