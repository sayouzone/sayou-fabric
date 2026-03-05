// Sayou Fabric — docs extras

// Smooth scroll offset fix for sticky header
document.addEventListener('DOMContentLoaded', function () {

  // Add copy feedback to code blocks
  document.querySelectorAll('.md-clipboard').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const original = btn.title;
      btn.title = 'Copied!';
      setTimeout(function () { btn.title = original; }, 1500);
    });
  });

  // Pipeline steps: subtle entrance animation
  const steps = document.querySelectorAll('.sf-pipeline__step');
  steps.forEach(function (step, i) {
    step.style.opacity = '0';
    step.style.transform = 'translateY(8px)';
    step.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    setTimeout(function () {
      step.style.opacity = '1';
      step.style.transform = 'translateY(0)';
    }, 80 + i * 60);
  });

  // Card entrance animation
  const cards = document.querySelectorAll('.sf-card');
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.style.opacity = '1';
          entry.target.style.transform = 'translateY(0)';
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });

    cards.forEach(function (card, i) {
      card.style.opacity = '0';
      card.style.transform = 'translateY(16px)';
      card.style.transition = `opacity 0.35s ease ${i * 0.07}s, transform 0.35s ease ${i * 0.07}s`;
      observer.observe(card);
    });
  }
});