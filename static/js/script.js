// Swipe functionality
let currentCard = 0;
const cards = document.querySelectorAll('.card');

function showCard(index) {
    cards.forEach((card, i) => {
        card.style.display = i === index ? 'block' : 'none';
    });

    updateSwipeButtons();
}

function updateSwipeButtons() {
    const likeBtn = document.getElementById('like-btn');
    const passBtn = document.getElementById('pass-btn');

    if (likeBtn && passBtn && cards.length > 0 && cards[currentCard]) {
        const userId = cards[currentCard].dataset.userId;

        likeBtn.onclick = () => window.location.href = `/like/${userId}`;
        passBtn.onclick = () => window.location.href = `/pass/${userId}`;
    }
}

if (cards.length > 0) {
    showCard(currentCard);
}

// Chat auto-scroll
const chatBox = document.querySelector('.chat-box');
if (chatBox) {
    chatBox.scrollTop = chatBox.scrollHeight;
}