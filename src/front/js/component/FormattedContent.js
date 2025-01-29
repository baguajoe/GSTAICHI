import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

const FormattedContent = ({ content }) => {
  if (!content) return null;
  
  return (
    <div className="content-wrapper">
      {content.split('\n').map((paragraph, index) => (
        paragraph.trim() && (
          <p key={index} className="mb-3">
            {paragraph}
          </p>
        )
      ))}
    </div>
  );
};

