'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { ChevronDown, X, Search } from 'lucide-react';

interface Option {
  value: string;
  label: string;
}

interface MultiSelectProps {
  label: string;
  values: string[];
  onChange: (values: string[]) => void;
  options: Option[];
  placeholder?: string;
  max?: number;
}

export function MultiSelect({
  label,
  values,
  onChange,
  options,
  placeholder = 'Select airports...',
  max = 8,
}: MultiSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const filteredOptions = options.filter(
    (o) => o.label.toLowerCase().includes(search.toLowerCase()) && !values.includes(o.value)
  );

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearch('');
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (isOpen && inputRef.current) inputRef.current.focus();
  }, [isOpen]);

  const handleAdd = useCallback(
    (value: string) => {
      if (values.length < max) {
        onChange([...values, value]);
      }
      setSearch('');
    },
    [values, onChange, max]
  );

  const handleRemove = useCallback(
    (value: string) => {
      onChange(values.filter((v) => v !== value));
    },
    [values, onChange]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Backspace' && search === '' && values.length > 0) {
        onChange(values.slice(0, -1));
      }
      if (e.key === 'Escape') {
        setIsOpen(false);
        setSearch('');
      }
    },
    [search, values, onChange]
  );

  return (
    <div ref={containerRef} className="relative" role="combobox" aria-expanded={isOpen} aria-haspopup="listbox">
      <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">{label}</label>
      <div
        className="w-full flex flex-wrap items-center gap-1.5 px-2 py-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm min-h-[38px] cursor-text focus-within:ring-2 focus-within:ring-primary-500"
        onClick={() => {
          setIsOpen(true);
          inputRef.current?.focus();
        }}
      >
        {values.map((val) => {
          const opt = options.find((o) => o.value === val);
          return (
            <span
              key={val}
              className="inline-flex items-center gap-1 px-2 py-0.5 bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 rounded-md text-xs font-medium"
            >
              {val}
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  handleRemove(val);
                }}
                className="hover:text-primary-900 dark:hover:text-primary-100"
                aria-label={`Remove ${opt?.label || val}`}
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          );
        })}
        <input
          ref={inputRef}
          type="text"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            if (!isOpen) setIsOpen(true);
          }}
          onKeyDown={handleKeyDown}
          placeholder={values.length === 0 ? placeholder : ''}
          className="flex-1 min-w-[60px] outline-none bg-transparent text-gray-900 dark:text-gray-100 placeholder-gray-400"
          aria-label="Search airports"
        />
        <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform flex-shrink-0 ${isOpen ? 'rotate-180' : ''}`} />
      </div>

      {isOpen && (
        <div className="absolute z-50 mt-1 w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg overflow-hidden" role="listbox">
          <div className="max-h-60 overflow-y-auto">
            {filteredOptions.length === 0 ? (
              <div className="px-3 py-2 text-sm text-gray-500 dark:text-gray-400">
                {values.length >= max ? `Maximum ${max} airports` : 'No results found'}
              </div>
            ) : (
              filteredOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  role="option"
                  aria-selected={false}
                  onClick={() => handleAdd(option.value)}
                  className="w-full flex items-center px-3 py-2 text-sm text-left text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50"
                >
                  <span className="font-medium text-primary-600 mr-2">{option.value}</span>
                  <span className="text-gray-500 dark:text-gray-400 truncate">
                    {option.label.replace(`${option.value} - `, '')}
                  </span>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
