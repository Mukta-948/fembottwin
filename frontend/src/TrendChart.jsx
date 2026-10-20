import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

export default function TrendChart({ observations }) {
  const points = observations.map((item) => ({
    time: new Date(item.observed_at).toLocaleString(),
    glucose: item.glucose,
  }));
  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={points}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="time" />
        <YAxis />
        <Tooltip />
        <Area type="monotone" dataKey="glucose" stroke="#438c7b" fill="#c7e7dc" />
      </AreaChart>
    </ResponsiveContainer>
  );
}
