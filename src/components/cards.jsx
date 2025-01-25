function Card({ title, value }) {
  return (
    <div className="card">
      <div className="info-text">{title}</div>
      <div className="number">{value}</div>
    </div>
  );
}

export default Card;
