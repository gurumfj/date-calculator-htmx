import React, { useState } from "react";

// SearchBar 元件屬性類型
interface SearchBarProps {
  onSearch: (searchKey: string) => void;
}

const SearchBar: React.FC<SearchBarProps> = ({ onSearch }) => {
  const [searchKey, setSearchKey] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(searchKey);
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <input
          type="search"
          value={searchKey}
          onChange={(e) => setSearchKey(e.target.value)}
          placeholder="搜尋批次"
        />
        <svg
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      </div>
    </form>
  );
};

export default SearchBar;
