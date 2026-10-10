import Button from "../../components/Button";
import { Empty } from "../../components/PageState";

export default function NotFound() {
  return (
    <Empty title="No encontramos esta página">
      <p>Puede que el enlace esté mal escrito o que la página ya no exista.</p>
      <Button to="/">Ir al inicio</Button>
    </Empty>
  );
}
