import React from "react";
import { useLocation } from "react-router-dom";
import { getCurrentRouteTitle } from "../utils/helpers";

const NavbarTitle: React.FC = () => {
  const location = useLocation();

  return (
    <h1
      className="
      absolute left-1/2 top-1/2 
      transform -translate-x-1/2 -translate-y-1/2 
      text-lg font-semibold text-gray-800
    "
    >
      {getCurrentRouteTitle(location.pathname)}
    </h1>
  );
};

export default NavbarTitle;
