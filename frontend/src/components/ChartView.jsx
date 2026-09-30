import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line
} from 'recharts';

const ChartView = ({ data, chartType = 'bar', title }) => {
  // Sample data structure for charts
  const chartData = data || [
    { name: 'Real News', value: 65 },
    { name: 'Fake News', value: 35 }
  ];

  const colors = ['#4CAF50', '#F44336', '#2196F3', '#FF9800', '#9C27B0'];

  const renderBarChart = () => (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="value" fill="#2196F3" />
      </BarChart>
    </ResponsiveContainer>
  );

  const renderPieChart = () => (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          outerRadius={100}
          fill="#8884d8"
          dataKey="value"
          label
        >
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );

  const renderLineChart = () => (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="value" stroke="#2196F3" strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  );

  const renderChart = () => {
    switch (chartType) {
      case 'pie':
        return renderPieChart();
      case 'line':
        return renderLineChart();
      case 'bar':
      default:
        return renderBarChart();
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      {title && (
        <h3 className="text-xl font-semibold text-gray-800 mb-4">
          {title}
        </h3>
      )}
      {renderChart()}
      
      {/* Statistics Summary */}
      <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-green-50 p-3 rounded-lg">
          <p className="text-green-800 font-semibold">Real News</p>
          <p className="text-2xl font-bold text-green-600">
            {chartData.find(d => d.name === 'Real News')?.value || 0}%
          </p>
        </div>
        <div className="bg-red-50 p-3 rounded-lg">
          <p className="text-red-800 font-semibold">Fake News</p>
          <p className="text-2xl font-bold text-red-600">
            {chartData.find(d => d.name === 'Fake News')?.value || 0}%
          </p>
        </div>
        <div className="bg-blue-50 p-3 rounded-lg">
          <p className="text-blue-800 font-semibold">Total Analyzed</p>
          <p className="text-2xl font-bold text-blue-600">
            {chartData.reduce((sum, item) => sum + item.value, 0)}
          </p>
        </div>
      </div>
    </div>
  );
};

export default ChartView;