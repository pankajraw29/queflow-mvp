import { Link } from "react-router-dom";

export default function Landing() {
  return (
    <div className="landing">
      <section className="hero">
        <div className="container">
          <h1 className="hero-title">
            End the line. <span className="accent">Keep the customers.</span>
          </h1>
          <p className="hero-sub">
            QueueFlow is a smart queue manager for clinics, salons, cafes and
            service counters. Customers scan a QR code, see their live position,
            and get called exactly when it is their turn — no crowding, no
            confusion.
          </p>
          <div className="hero-ctas">
            <Link to="/register" className="btn btn-primary btn-lg">
              Create your first queue
            </Link>
            <Link to="/login" className="btn btn-outline btn-lg">
              Log in
            </Link>
          </div>
        </div>
      </section>

      <section className="container steps-section">
        <h2 className="section-title">How it works</h2>
        <div className="steps">
          <div className="step-card">
            <div className="step-num">1</div>
            <h3>Create a queue</h3>
            <p>
              Sign up, name your service counter, and get a unique QR code and
              join link for that queue.
            </p>
          </div>
          <div className="step-card">
            <div className="step-num">2</div>
            <h3>Customers join by scanning</h3>
            <p>
              Customers scan the QR, enter their name, and instantly get a
              ticket number with their live position in line.
            </p>
          </div>
          <div className="step-card">
            <div className="step-num">3</div>
            <h3>You call, they come</h3>
            <p>
              Tap “Call Next” on your dashboard. The customer’s phone lights up
              with “It’s your turn!” — automatically.
            </p>
          </div>
        </div>
      </section>

      <section className="container features-section">
        <div className="features">
          <div className="feature">
            <h3>📱 No app needed</h3>
            <p>Customers join from their browser. Zero installs, zero friction.</p>
          </div>
          <div className="feature">
            <h3>⚡ Live updates</h3>
            <p>Ticket positions refresh in real time as the queue moves.</p>
          </div>
          <div className="feature">
            <h3>🎛️ Full control</h3>
            <p>Call next, complete, skip or reset — and open or close queues anytime.</p>
          </div>
        </div>
      </section>
    </div>
  );
}
