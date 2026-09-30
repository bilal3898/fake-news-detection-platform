// src/components/Sidebar.jsx
import React from "react";
import { NavLink } from "react-router-dom";
import {
  Home,
  BarChart,
  Users,
  Settings,
  LogOut,
} from "lucide-react"; // modern icons

const Sidebar = () => {
  return (
    <div className="h-screen w-64 bg-gray-900 text-white flex flex-col fixed left-0 top-0 pt-16 shadow-lg">
      {/* Sidebar content */}
      <nav className="flex-1 px-4 py-6 space-y-4">
        <NavLink
          to="/dashboard"
          className={({ isActive }) =>
            `flex items-center px-3 py-2 rounded-lg hover:bg-gray-800 transition ${
              isActive ? "bg-gray-800" : ""
            }`
          }
        >
          <Home className="w-5 h-5 mr-2" />
          Dashboard
        </NavLink>

        <NavLink
          to="/analytics"
          className={({ isActive }) =>
            `flex items-center px-3 py-2 rounded-lg hover:bg-gray-800 transition ${
              isActive ? "bg-gray-800" : ""
            }`
          }
        >
          <BarChart className="w-5 h-5 mr-2" />
          Analytics
        </NavLink>

        <NavLink
          to="/users"
          className={({ isActive }) =>
            `flex items-center px-3 py-2 rounded-lg hover:bg-gray-800 transition ${
              isActive ? "bg-gray-800" : ""
            }`
          }
        >
          <Users className="w-5 h-5 mr-2" />
          Users
        </NavLink>

        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `flex items-center px-3 py-2 rounded-lg hover:bg-gray-800 transition ${
              isActive ? "bg-gray-800" : ""
            }`
          }
        >
          <Settings className="w-5 h-5 mr-2" />
          Settings
        </NavLink>
      </nav>

      {/* Logout button at bottom */}
      <div className="p-4 border-t border-gray-700">
        <button className="w-full flex items-center px-3 py-2 rounded-lg bg-red-600 hover:bg-red-700 transition">
          <LogOut className="w-5 h-5 mr-2" />
          Logout
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
