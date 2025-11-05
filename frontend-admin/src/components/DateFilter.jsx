import React from 'react'
import { Filter } from 'lucide-react'

const DateFilter = ({ tabName, dateFilters, setDateFilters, onApply, onClear }) => {
  const hasFilters = dateFilters[tabName]?.startDate || dateFilters[tabName]?.endDate

  return (
    <div className="date-filter-container">
      <div className="date-filter-group">
        <Filter size={18} />
        <label>Start Date:</label>
        <input
          type="date"
          value={dateFilters[tabName]?.startDate || ''}
          onChange={(e) => setDateFilters(prev => ({
            ...prev,
            [tabName]: { ...prev[tabName], startDate: e.target.value }
          }))}
        />
        <label>End Date:</label>
        <input
          type="date"
          value={dateFilters[tabName]?.endDate || ''}
          onChange={(e) => setDateFilters(prev => ({
            ...prev,
            [tabName]: { ...prev[tabName], endDate: e.target.value }
          }))}
        />
        <button
          className="btn btn-primary"
          onClick={() => onApply(tabName)}
        >
          Apply Filter
        </button>
        {hasFilters && (
          <button
            className="btn btn-secondary"
            onClick={() => onClear(tabName)}
          >
            Clear
          </button>
        )}
      </div>
    </div>
  )
}

export default DateFilter

