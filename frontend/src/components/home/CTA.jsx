import React, { useEffect, useState } from 'react';

const CTA = () => {
  const [timeLeft, setTimeLeft] = useState({ days: '--', hours: '--', minutes: '--', seconds: '--' });

  useEffect(() => {
    // Simple countdown to a fixed date (can be made configurable)
    const target = new Date('2025-12-31T23:59:59').getTime();

    const tick = () => {
      const now = Date.now();
      const diff = Math.max(0, target - now);
      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
      const minutes = Math.floor((diff / (1000 * 60)) % 60);
      const seconds = Math.floor((diff / 1000) % 60);
      setTimeLeft({ days, hours, minutes, seconds });
    };

    tick();
    const t = setInterval(tick, 1000);
    return () => clearInterval(t);
  }, []);

  return (
    <section id="call-to-action" className="call-to-action section">
      <div className="container" data-aos="fade-up" data-aos-delay="100">
        <div className="row">
          <div className="col-lg-8 mx-auto">
            <div className="main-content text-center" data-aos="zoom-in" data-aos-delay="200">
              <div className="offer-badge" data-aos="fade-down" data-aos-delay="250">
                <span className="limited-time">Limited Time</span>
                <span className="offer-text">50% OFF</span>
              </div>

              <h2 data-aos="fade-up" data-aos-delay="300">Exclusive Flash Sale</h2>

              <p className="subtitle" data-aos="fade-up" data-aos-delay="350">Don't miss out on our biggest sale of the year. Premium quality products at unbeatable prices for the next 48 hours only.</p>

              <div className="countdown-wrapper" data-aos="fade-up" data-aos-delay="400">
                <div className="countdown d-flex justify-content-center">
                  <div>
                    <h3 className="count-days">{timeLeft.days}</h3>
                    <h4>Days</h4>
                  </div>
                  <div>
                    <h3 className="count-hours">{timeLeft.hours}</h3>
                    <h4>Hours</h4>
                  </div>
                  <div>
                    <h3 className="count-minutes">{timeLeft.minutes}</h3>
                    <h4>Minutes</h4>
                  </div>
                  <div>
                    <h3 className="count-seconds">{timeLeft.seconds}</h3>
                    <h4>Seconds</h4>
                  </div>
                </div>
              </div>

              <div className="action-buttons" data-aos="fade-up" data-aos-delay="450">
                <a href="#" className="btn-shop-now">Shop Now</a>
                <a href="#" className="btn-view-deals">View All Deals</a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default CTA;
