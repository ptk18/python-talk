import Navbar from "../components/Navbar";
import "./styles/Profile.css";

export default function Profile() {
    return (
        <div className="profile__viewport">
            {/* Top bar */}
            <Navbar rightButton={{ text: "Chat", to: "/chat" }} />

            {/* Main container */}
            <main className="profile__main">
                <div className="profile__panel">
                    {/* Left side: profile picture placeholder */}
                    <aside className="profile__sidebar">
                        <div className="profile__picBox">
                            <span>Profile<br />Picture</span>
                        </div>
                    </aside>

                    {/* Right side: info form */}
                    <section className="profile__content">
                        <div className="profile__header">
                            <h1>Profile</h1>
                            <button className="profile__edit">Edit</button>
                        </div>

                        <form className="profile__form">
                            <div className="profile__field">
                                <label>Name</label>
                                <input type="text" disabled />
                            </div>

                            <div className="profile__field">
                                <label>Surname</label>
                                <input type="text" disabled />
                            </div>

                            <div className="profile__field">
                                <label>Email</label>
                                <input type="email" disabled />
                            </div>

                            <div className="profile__field">
                                <label>Mobile number</label>
                                <input type="text" disabled />
                            </div>

                            <div className="profile__field">
                                <label>Address</label>
                                <textarea disabled />
                            </div>
                        </form>
                    </section>
                </div>
            </main>
        </div>
    );
}
