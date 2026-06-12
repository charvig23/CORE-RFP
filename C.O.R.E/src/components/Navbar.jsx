import logo from "../assets/logo_core.png"; // path adjust if needed
import "./Navbar.css";

function Navbar() {
  return (
    <nav className="navbar">
      <div className="nav-left">
        <img src={logo} alt="Logo" className="nav-logo" />

        <div className="nav-title">
          C.O.R.E (Central Orchestration & RFP Engine) FMCG RFP Assistant
        </div>
      </div>

      <div className="nav-links">
        <span>Inbox</span>
        <span>Chat</span>
        <span>Processing</span>
        <span>Proposal</span>
      </div>
    </nav>
  );
}

export default Navbar;
