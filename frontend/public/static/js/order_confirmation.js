document.addEventListener('DOMContentLoaded', function() {
  console.log('Order confirmation page initialized with account layout');
  if (typeof AOS !== 'undefined') {
    AOS.init({
      duration: 800,
      easing: 'ease-in-out',
      once: true,
      mirror: false
    });
  }
  const successAnimation = document.querySelector('.success-animation');
  if (successAnimation) {
    successAnimation.style.opacity = '0';
    successAnimation.style.transform = 'scale(0.5)';
    setTimeout(() => {
      successAnimation.style.transition = 'all 0.6s ease';
      successAnimation.style.opacity = '1';
      successAnimation.style.transform = 'scale(1)';
    }, 300);
  }
  setTimeout(() => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  }, 100);
  const cards = document.querySelectorAll('.card, .details-card');
  cards.forEach(card => {
    card.addEventListener('mouseenter', function() {
      this.style.transform = 'translateY(-2px)';
      this.style.boxShadow = '0 4px 15px rgba(0,0,0,0.1)';
      this.style.transition = 'all 0.2s ease';
    });
    card.addEventListener('mouseleave', function() {
      this.style.transform = 'translateY(0)';
      this.style.boxShadow = '';
    });
  });
  const cardHeaders = document.querySelectorAll('.card-header[data-toggle="collapse"]');
  cardHeaders.forEach(header => {
    header.addEventListener('click', function() {
      const cardBody = this.nextElementSibling;
      const toggleIcon = this.querySelector('.toggle-icon');
      if (cardBody.style.display === 'none' || cardBody.style.display === '') {
        cardBody.style.display = 'block';
        toggleIcon.classList.remove('bi-chevron-down');
        toggleIcon.classList.add('bi-chevron-up');
      } else {
        cardBody.style.display = 'none';
        toggleIcon.classList.remove('bi-chevron-up');
        toggleIcon.classList.add('bi-chevron-down');
      }
    });
  });
  const printOrder = () => {
    window.print();
  };
  const downloadOrderPDF = () => {
    alert('PDF download feature will be available soon!');
  };
  const shareOrder = () => {
    if (navigator.share) {
      navigator.share({
        title: `Order Confirmation - ${document.querySelector('.order-id h4').textContent}`,
        text: 'Check out my order confirmation from Pavitra Enterprises',
        url: window.location.href
      })
      .catch(error => console.log('Error sharing:', error));
    } else {
      navigator.clipboard.writeText(window.location.href)
        .then(() => alert('Order link copied to clipboard!'))
        .catch(err => console.error('Failed to copy: ', err));
    }
  };
  const trackOrder = () => {
    const orderNumber = document.querySelector('.order-id h4').textContent.replace('Order #', '');
    alert(`Tracking for order ${orderNumber} will be available once your order is shipped!`);
  };
  window.printOrder = printOrder;
  window.downloadOrderPDF = downloadOrderPDF;
  window.shareOrder = shareOrder;
  window.trackOrder = trackOrder;
  const simulateOrderUpdates = () => {
    const statusElements = document.querySelectorAll('.stepper-item');
    let currentStep = 1;
    const updateStep = () => {
      if (currentStep <= statusElements.length) {
        statusElements.forEach((step, index) => {
          if (index < currentStep) {
            step.classList.add('completed');
            step.classList.remove('current');
          } else if (index === currentStep) {
            step.classList.add('current');
          } else {
            step.classList.remove('completed', 'current');
          }
        });
        currentStep++;
      }
    };
    if (window.location.search.includes('demo=true')) {
      setInterval(updateStep, 5000);
    }
  };
  simulateOrderUpdates();
  console.log('Order confirmation page fully initialized with account layout');
});