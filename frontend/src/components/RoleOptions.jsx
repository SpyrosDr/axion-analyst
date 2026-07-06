import { roleLabel } from "../roles";

function RoleOptions({ roles }) {
  return roles.map((role) => (
    <option key={role} value={role}>
      {roleLabel(role)}
    </option>
  ));
}

export default RoleOptions;
