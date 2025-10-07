import "./Home.css";

export default function Home() {
  return (
    <div className="home__container">
      {/* NAVBAR */}
      <header className="home__navbar">
        <h1 className="home__logo">PyTalk</h1>

        <nav className="home__links">
          <a href="#" className="is-active">Home</a>
          <a href="#">Setting</a>
          <a href="#">Profile</a>
        </nav>

        <button className="home__login">LOGIN</button>
      </header>

      {/* HERO */}
      <section className="home__hero">
        <div className="home__heroOverlay">
          <h2 className="home__heroTitle">PYTALK</h2>
          <p className="home__heroSubtitle">
            Convenient platform to talk with python in real life
          </p>
        </div>
      </section>
    </div>
  );
}
