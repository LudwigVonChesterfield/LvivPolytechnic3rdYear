Attribute VB_Name = "Module1"
Sub Chart()
    With Charts.Add
        .SetSourceData Source:=Worksheets(1).Range("A1:F26")
        .HasTitle = True
        .ChartTitle.Text = "State Chart"
        .Activate
'
' Chart Macro
' plot a graph
'
' Keyboard Shortcut: Ctrl+e
'
    End With
End Sub

