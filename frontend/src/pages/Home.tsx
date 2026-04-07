import { useNavigate } from 'react-router-dom';
import { useAppDispatch } from '../store/hooks';
import { logout } from '../store/slices/authSlice';

export default function Home() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  const handleLogout = () => {
    dispatch(logout());
    navigate('/login', { replace: true });
  };

  return (
    <div>
      <h1>CloudStorm</h1>
      <button onClick={handleLogout}>Sign out</button>
    </div>
  );
}
