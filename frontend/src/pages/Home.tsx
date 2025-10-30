import Navbar from "../components/Navbar";
import "./styles/Home.css";

export default function Home() {
    return (
        <div className="home__container">
            {/* NAVBAR */}
            <Navbar rightButton={{ text: "LOGIN", to: "/login" }} />

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
