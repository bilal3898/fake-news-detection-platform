// src/components/NavItem.jsx
import React from "react";
import { NavLink } from "react-router-dom";

const NavItem = ({ icon: Icon, label, to }) => {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `nav-item ${isActive ? "nav-item-active" : ""}`
      }
    >
      <Icon className="w-5 h-5" />
      <span>{label}</span>
    </NavLink>
  );
};

export default NavItem;
