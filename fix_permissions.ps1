
$path = "c:\Users\Headsprung\.ssh\google_compute_engine"
$user = $env:USERNAME
Write-Host "Fixing permissions for $path for user $user..."

$acl = Get-Acl $path
# Disable inheritance and remove existing inherited rules
$acl.SetAccessRuleProtection($true, $false)

# Create new rule for current user
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule($user, "FullControl", "Allow")
$acl.SetAccessRule($rule)

# Apply
Set-Acl $path $acl
Write-Host "Permissions fixed."
