package com.binus.ootd;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.RequiresApi;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.database.DatabaseReference;
import com.google.firebase.database.FirebaseDatabase;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

public class EventEditActivity extends AppCompatActivity {
    private EditText event_name;
    private TextView date;

    private FirebaseDatabase rootNode;
    private DatabaseReference taskReference;

    private FirebaseAuth mAuth;

    @RequiresApi(api = Build.VERSION_CODES.O)
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_event_edit);
        initWidgets();

        mAuth = FirebaseAuth.getInstance();
        rootNode = FirebaseDatabase.getInstance();

        FirebaseUser user = mAuth.getCurrentUser();
        taskReference = rootNode.getReference("tasks").child(user.getUid());

        date.setText(String.format("Date : %s", formattedDate(YourTaskActivity.selectedDate)));
    }

    @RequiresApi(api = Build.VERSION_CODES.O)
    private String formattedDate(LocalDate date) {
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("dd MMM yyyy");
        return date.format(formatter);
    }

    private void initWidgets() {
        event_name = findViewById(R.id.event_name);
        date = findViewById(R.id.date);
    }

    @RequiresApi(api = Build.VERSION_CODES.O)
    public void AddEventAction(View view) {
        String taskname = event_name.getText().toString();

        if(taskname.isEmpty()) {
            Toast.makeText(getApplicationContext(), "fill task name", Toast.LENGTH_SHORT).show();
        }
        else {
            Task newTask = new Task(taskname);
            taskReference.child(YourTaskActivity.selectedDate.toString())
                    .child(taskname)
                    .setValue(newTask);

            Intent refresh = new Intent(this, YourTaskActivity.class);
            startActivity(refresh);
            finish();
        }
    }

    public void back(View view) {
        startActivity(new Intent(this, YourTaskActivity.class));
        finish();
    }

    @Override
    public void onBackPressed() {
        super.onBackPressed();
        startActivity(new Intent(this, YourTaskActivity.class));
        finish();
    }

}
