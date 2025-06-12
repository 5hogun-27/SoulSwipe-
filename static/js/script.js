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
        passBtn.onclick = () => {
            currentCard++;
            if (currentCard < cards.length) {
                showCard(currentCard);
            } else {
                document.querySelector('.swipe-buttons').style.display = 'none';
                document.querySelector('.container').innerHTML += '<p>No more users to swipe!</p>';
            }
        };
    }
}

// Initialize
if (cards.length > 0) {
    showCard(currentCard);
}