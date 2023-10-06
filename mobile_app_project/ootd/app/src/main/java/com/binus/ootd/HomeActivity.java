package com.binus.ootd;

import androidx.annotation.NonNull;
import androidx.appcompat.app.ActionBarDrawerToggle;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;
import androidx.core.view.GravityCompat;
import androidx.customview.widget.ViewDragHelper;
import androidx.drawerlayout.widget.DrawerLayout;
import androidx.recyclerview.widget.DefaultItemAnimator;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.graphics.Point;
import android.os.Bundle;
import android.text.TextUtils;
import android.util.Log;
import android.view.MenuItem;
import android.view.View;
import android.widget.Button;
import android.widget.ImageButton;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import com.google.android.material.navigation.NavigationView;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.database.DataSnapshot;
import com.google.firebase.database.DatabaseError;
import com.google.firebase.database.DatabaseReference;
import com.google.firebase.database.FirebaseDatabase;
import com.google.firebase.database.ValueEventListener;
import com.huawei.agconnect.config.AGConnectServicesConfig;
import com.huawei.hms.aaid.HmsInstanceId;
import com.huawei.hms.analytics.HiAnalytics;
import com.huawei.hms.analytics.HiAnalyticsInstance;
import com.huawei.hms.analytics.HiAnalyticsTools;
import com.huawei.hms.common.ApiException;

import java.lang.reflect.Field;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;

public class HomeActivity extends AppCompatActivity{
    private RecyclerView taskRecyclerView;
    private TextView name_textview, no_task_textview;
    private String name;
    private LocalDate selectedDate;

    private ImageButton homeButton, taskButton, myProfileButton;

    private FirebaseAuth mAuth;
    private FirebaseDatabase rootNode;
    private DatabaseReference userReference;
    private DatabaseReference todayTaskReference;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_home);

        taskRecyclerView = findViewById(R.id.task_list_recycler);
        name_textview = findViewById(R.id.name_textview);
        no_task_textview = findViewById(R.id.no_task_text);
        homeButton = findViewById(R.id.home_button);
        taskButton = findViewById(R.id.task_button);
        myProfileButton = findViewById(R.id.profile_button);

        mAuth = FirebaseAuth.getInstance();
        rootNode = FirebaseDatabase.getInstance();
        selectedDate = LocalDate.now();

        FirebaseUser user = mAuth.getCurrentUser();
        userReference = rootNode.getReference("users").child(user.getUid());
        todayTaskReference = rootNode.getReference("tasks").child(user.getUid()).child(selectedDate.toString());

        userReference.addValueEventListener(new ValueEventListener() {
            @Override
            public void onDataChange(@NonNull DataSnapshot snapshot) {
                User currentUser = snapshot.getValue(User.class);

                name = currentUser.getName();
                name_textview.setText(name);
            }

            @Override
            public void onCancelled(@NonNull DatabaseError error) {
                Toast.makeText(HomeActivity.this, "Fail to fetch user's data!", Toast.LENGTH_SHORT).show();
            }
        });

        homeButton.isSelected();
        homeButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                recreate();
            }
        });

        taskButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                startActivity(new Intent(HomeActivity.this, YourTaskActivity.class));
                finish();
            }
        });

        myProfileButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                startActivity(new Intent(HomeActivity.this, ProfileActivity.class));
                finish();
            }
        });

        // Temporary Task List Data
        todayTaskReference = rootNode.getReference("tasks").child(user.getUid()).child(selectedDate.toString());

        ValueEventListener postListener = new ValueEventListener() {
            @Override
            public void onDataChange(DataSnapshot dataSnapshot) {
                Iterable<DataSnapshot> taskList = dataSnapshot.getChildren();
                ArrayList<Task> dailyTasks = new ArrayList<>();

                for(DataSnapshot task:taskList) {
                    dailyTasks.add(new Task(task.getKey()));
                }

                TaskRecyclerAdapter adapter = new TaskRecyclerAdapter(dailyTasks);
                RecyclerView.LayoutManager layoutManager = new LinearLayoutManager(getApplicationContext());
                taskRecyclerView.setLayoutManager(layoutManager);
                taskRecyclerView.setItemAnimator(new DefaultItemAnimator());
                taskRecyclerView.setAdapter(adapter);

                if (dailyTasks.isEmpty()) {
                    no_task_textview.setVisibility(View.VISIBLE);
                    taskRecyclerView.setVisibility(View.GONE);
                }
                else {
                    no_task_textview.setVisibility(View.GONE);
                    taskRecyclerView.setVisibility(View.VISIBLE);
                }
            }

            @Override
            public void onCancelled(DatabaseError databaseError) {

            }
        };
        todayTaskReference.addValueEventListener(postListener);

    }

    public void more(View view) {
        startActivity(new Intent(this, YourTaskActivity.class));
        finish();
    }

    @Override
    public void onBackPressed() {
        super.onBackPressed();
        finish();
    }
}