import { useState, useEffect } from "react";
import Navbar from "../components/Navbar";
import "./styles/Profile.css";
import { useAuth } from "../context/AuthContext";
import { userAPI, type UserProfile, type UserProfileUpdate } from "../services/api";

export default function Profile() {
    const { user } = useAuth();
    const [profile, setProfile] = useState<UserProfile | null>(null);
    const [isEditing, setIsEditing] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    // Form state
    const [formData, setFormData] = useState({
        username: "",
        email: "",
    });

    useEffect(() => {
        if (user) {
            fetchProfile();
        }
    }, [user]);

    const fetchProfile = async () => {
        if (!user) return;

        try {
            setLoading(true);
            const data = await userAPI.getProfile(user.id);
            setProfile(data);
            setFormData({
                username: data.username || "",
                email: data.email || "",
            });
        } catch (err: any) {
            console.error("Failed to fetch profile:", err);
            setError("Failed to load profile data");
        } finally {
            setLoading(false);
        }
    };

    const handleEdit = () => {
        setIsEditing(true);
    };

    const handleCancel = () => {
        if (profile) {
            setFormData({
                username: profile.username || "",
                email: profile.email || "",
            });
        }
        setIsEditing(false);
    };

    const handleSave = async () => {
        if (!user) return;

        try {
            const updateData: UserProfileUpdate = {
                username: formData.username || undefined,
                email: formData.email || undefined,
            };

            const updatedProfile = await userAPI.updateProfile(user.id, updateData);
            setProfile(updatedProfile);
            setIsEditing(false);
            alert("Profile updated successfully!");
        } catch (err: any) {
            console.error("Failed to update profile:", err);
            alert("Failed to update profile: " + err.message);
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value,
        });
    };

    if (loading) {
        return (
            <div className="profile__viewport">
                <Navbar rightButton={{ text: "Chat", to: "/chat" }} />
                <main className="profile__main">
                    <p>Loading profile...</p>
                </main>
            </div>
        );
    }

    if (error) {
        return (
            <div className="profile__viewport">
                <Navbar rightButton={{ text: "Chat", to: "/chat" }} />
                <main className="profile__main">
                    <p style={{ color: "red" }}>{error}</p>
                </main>
            </div>
        );
    }

    return (
        <div className="profile__viewport">
            {/* Top bar */}
            <Navbar rightButton={{ text: "Chat", to: "/chat" }} />

            {/* Main container */}
            <main className="profile__main">
                <div className="profile__panel">
                    {/* Right side: info form */}
                    <section className="profile__content">
                        <div className="profile__header">
                            <h1>Profile</h1>
                            {!isEditing ? (
                                <button className="profile__edit" onClick={handleEdit}>
                                    Edit
                                </button>
                            ) : (
                                <div style={{ display: "flex", gap: "8px" }}>
                                    <button className="profile__save" onClick={handleSave}>
                                        Save
                                    </button>
                                    <button className="profile__cancel" onClick={handleCancel}>
                                        Cancel
                                    </button>
                                </div>
                            )}
                        </div>

                        <form className="profile__form" onSubmit={(e) => e.preventDefault()}>
                            <div className="profile__field">
                                <label>Username</label>
                                <input
                                    type="text"
                                    name="username"
                                    value={formData.username}
                                    onChange={handleChange}
                                    disabled={!isEditing}
                                />
                            </div>

                            <div className="profile__field">
                                <label>Email</label>
                                <input
                                    type="email"
                                    name="email"
                                    value={formData.email}
                                    onChange={handleChange}
                                    disabled={!isEditing}
                                />
                            </div>
                        </form>
                    </section>
                </div>
            </main>
        </div>
    );
}
